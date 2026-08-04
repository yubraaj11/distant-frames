import cv2
import os
from pathlib import Path

_CASCADES_DIR = Path(__file__).parent / "haarcascade_classifiers"

def _load_eye_cascades():
    """Load and return (face_cascade, eye_cascade) from the local haarcascade_classifiers/ directory."""
    face_path = str(_CASCADES_DIR / "haarcascade_frontalface_default.xml")
    eye_path = str(_CASCADES_DIR / "haarcascade_eye.xml")
    face_cascade = cv2.CascadeClassifier(face_path)
    eye_cascade = cv2.CascadeClassifier(eye_path)
    if face_cascade.empty() or eye_cascade.empty():
        raise RuntimeError(
            f"Failed to load Haar cascade classifiers from {_CASCADES_DIR}. "
            "Ensure haarcascade_frontalface_default.xml and haarcascade_eye.xml exist there."
        )
    return face_cascade, eye_cascade

def has_open_eyes(frame, face_cascade, eye_cascade):
    """Return True if at least one face with two detected (open) eyes is found in the frame."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    for (x, y, w, h) in faces:
        roi = gray[y:y + h, x:x + w]
        eyes = eye_cascade.detectMultiScale(roi, scaleFactor=1.1, minNeighbors=5)
        if len(eyes) >= 2:
            return True
    return False

def _colour_histogram(frame):
    """Builds the normalized HSV Hue/Saturation histogram used for comparison.

    Split out from `calculate_similarity` so the extraction loop can compute a
    reference frame's histogram once per segment instead of once per comparison.

    Args:
        frame: A video frame (BGR image/numpy array).

    Returns:
        The normalized 180x256 Hue/Saturation histogram.
    """
    # Convert to HSV for better color handling, or Gray if color doesn't matter much.
    # HSV is generally more robust to lighting changes than BGR.
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Calculate histogram
    # Channels 0 and 1 (Hue and Saturation) are usually enough
    hist = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])

    # Normalize histogram
    cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
    return hist

def calculate_similarity(frame1, frame2):
    """Calculates similarity between two frames using Histogram Correlation.

    Converts frames to HSV color space and compares their normalized histograms.
    This method is generally robust to lighting changes.

    Args:
        frame1: The first video frame (BGR image/numpy array).
        frame2: The second video frame (BGR image/numpy array).

    Returns:
        float: A similarity score between 0.0 (distinct) and 1.0 (identical).
    """
    return cv2.compareHist(
        _colour_histogram(frame1), _colour_histogram(frame2), cv2.HISTCMP_CORREL
    )

# --- Refinement stage (opt-in, --refine) -------------------------------------
# The Hue/Saturation histogram has a known blind spot: flat graphic content has
# near-zero saturation, so a hard cut between two flat frames of different
# brightness (white to black) produces near-identical histograms and scores
# ~1.0. A whole-scene change is then silently dropped.
#
# The guard below closes that hole without replacing the histogram. It can only
# ever *escalate* a would-be SKIP to a second-stage descriptor check, never
# decide on its own, so the histogram still decides every frame it is good at
# and `--threshold` keeps its meaning. The second stage can only turn a SKIP
# into a SAVE, never the reverse: a missed scene change is unrecoverable, a
# redundant frame is cheap.

_THUMB_SIZE = 64
_GUARD_TILES = 8               # 8x8 grid over the thumbnail
_GUARD_DELTA_CUTOFF = 4.0      # worst-tile |BGR| difference (0-255) that triggers stage 1
_FLAT_EPSILON = 6.0            # Laplacian magnitude below which a pixel reads as flat
_FLAT_FRACTION_CUTOFF = 0.45   # at or above this the frame is treated as graphic content
_HOG_IMAGE_SIZE = 128
_HOG_DISTANCE_CUTOFF = 0.35    # L2 between unit-norm HOG vectors (range 0-2)
_COLOUR_DISTINCT_DELTA = 60.0  # worst-tile colour shift HOG cannot see, decided on colour alone
_ORB_FEATURES = 400
_ORB_HAMMING_CUTOFF = 48       # a 256-bit descriptor pair closer than this is "the same point"
_ORB_MATCH_CUTOFF = 0.55       # below this share of reference keypoints matched, call it distinct

# Settling. On animated content a descriptor cannot tell "an element moved" from
# "the content changed" - measured, the two classes overlap by -0.118 and no
# cutoff separates them, matching the -0.116 the blur metric was measured at.
# Consecutive samples do separate them cleanly: while a title flies in, adjacent
# samples differ by 7.7-32.7, and once it lands they differ by 0.0-0.5. So a
# distinct frame is held until the picture stops moving, and the settled frame is
# saved instead of the mid-transition one that triggered the change.
_SETTLE_DELTA = 4.0            # consecutive-sample worst-tile delta below which motion has stopped
_SETTLE_MAX_WAIT = 8           # samples to wait for settling before saving anyway, so that
                               # continuously animating content cannot lose a scene entirely

_HOG = cv2.HOGDescriptor(
    (_HOG_IMAGE_SIZE, _HOG_IMAGE_SIZE),  # winSize
    (32, 32),                            # blockSize
    (16, 16),                            # blockStride
    (16, 16),                            # cellSize
    9,                                   # nbins
)
_ORB = cv2.ORB_create(nfeatures=_ORB_FEATURES)
# ORB descriptors are binary, so Hamming is the matching metric - L2 over
# unpacked bits is monotonically equivalent but throws away the popcount path
# that makes ORB cheap in the first place.
_ORB_MATCHER = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

def _thumbnail(frame):
    """Downscales a frame to the square thumbnail the guard and router work on."""
    return cv2.resize(frame, (_THUMB_SIZE, _THUMB_SIZE), interpolation=cv2.INTER_AREA)

def _colour_delta(thumb1, thumb2):
    """Returns the largest per-tile mean absolute BGR difference (0-255).

    Worst tile, not whole-frame mean. A title changing on an otherwise static
    slide alters only a few percent of the picture, so any frame-wide average
    stays near zero and the change never escalates - the same failure the
    histogram already has. Measured on the reference video, a slide-to-slide
    text change scores 1.14 as a frame mean but 22.36 as a worst tile, against
    0.27 for a true duplicate.

    Colour rather than luminance: an equal-brightness cut between two saturated
    colours is invisible to a grayscale comparison.
    """
    diff = cv2.absdiff(thumb1, thumb2)
    step = diff.shape[0] // _GUARD_TILES
    return max(
        float(diff[y:y + step, x:x + step].mean())
        for y in range(0, step * _GUARD_TILES, step)
        for x in range(0, step * _GUARD_TILES, step)
    )

def _flat_fraction(thumb):
    """Returns the share of the thumbnail sitting in near-uniform regions.

    Used to route between descriptors. Keypoint detectors need texture, and
    slide-style content does not have it - what few keypoints a slide yields sit
    on the deck template (logo, rules, footer), which is identical across every
    slide, so ORB reports two different slides as a near-perfect match. Flat
    content therefore goes to the dense descriptor instead.

    Args:
        thumb: A thumbnail produced by `_thumbnail`.

    Returns:
        float: Fraction between 0.0 (fully textured) and 1.0 (fully flat).
    """
    gray = cv2.cvtColor(thumb, cv2.COLOR_BGR2GRAY)
    detail = cv2.Laplacian(gray, cv2.CV_32F)
    return float((abs(detail) < _FLAT_EPSILON).mean())

def _hog_vector(frame):
    """Returns a unit-norm HOG descriptor for the whole frame."""
    resized = cv2.resize(frame, (_HOG_IMAGE_SIZE, _HOG_IMAGE_SIZE), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    vector = _HOG.compute(gray)
    norm = cv2.norm(vector, cv2.NORM_L2)
    return vector / norm if norm > 0 else vector

def _orb_descriptors(frame):
    """Returns ORB descriptors for a frame, or None when it yields no keypoints."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, descriptors = _ORB.detectAndCompute(gray, None)
    return descriptors

def _stage1_signature(frame, use_hog):
    """Computes whichever descriptor the router picked for this segment."""
    return _hog_vector(frame) if use_hog else _orb_descriptors(frame)

def _stage1_is_distinct(reference, candidate, use_hog, colour_delta):
    """Decides whether two stage-1 signatures represent different content.

    Args:
        reference: Signature of the frame that started the current segment.
        candidate: Signature of the frame being tested.
        use_hog: True for the dense HOG/L2 path, False for the ORB/Hamming path.
        colour_delta: Worst-tile colour difference from `_colour_delta`.

    Returns:
        bool: True when the frame should be treated as a new scene.
    """
    if use_hog:
        # HOG is gradient orientation on luminance, so a cut between two flat
        # frames of different colour has no gradients on either side and scores
        # 0.0 - measured at exactly that for both red->blue and white->black.
        # A region-scale colour shift is therefore decided on colour alone.
        # Only on this route: on textured footage a bright object moving through
        # frame produces the same signal, and there ORB is the better judge.
        if colour_delta >= _COLOUR_DISTINCT_DELTA:
            return True
        return cv2.norm(reference, candidate, cv2.NORM_L2) > _HOG_DISTANCE_CUTOFF

    if reference is None or candidate is None or len(reference) == 0:
        # No keypoints to reason about; defer to the histogram's SKIP.
        return False
    matches = _ORB_MATCHER.match(reference, candidate)
    close = sum(1 for match in matches if match.distance <= _ORB_HAMMING_CUTOFF)
    return close / len(reference) < _ORB_MATCH_CUTOFF

def extract_frames(video_path, output_folder, threshold=0.78, start_time=0.0, open_eyes_only=False,
                   refine=False):
    """Extracts distinct frames from a video file based on visual similarity.

    The function samples the video at 1-second intervals starting from
    `start_time`. It compares the current frame with the last saved frame.
    If the similarity score is below the specified threshold, the frame is
    considered distinct and saved.

    If a frame is skipped (similar to the last saved frame), the next comparison
    will be performed against the *previous* saved frame (if available) to ensure
    robustness against gradual changes or local similarities.

    Args:
        video_path (str): Path to the input video file.
        output_folder (str): Directory where extracted frames will be saved.
            The directory will be created if it does not exist.
        threshold (float, optional): Similarity threshold (0.0 to 1.0).
            Frames with similarity higher than this value regarding the last
            saved frame will be dropped, so raising it keeps more frames.
            Defaults to 0.78.
        start_time (float, optional): Timestamp in seconds from which to begin
            extraction. Defaults to 0.0 (beginning of video).
        open_eyes_only (bool, optional): When True, only frames where at least
            one face with two open eyes is detected are saved. Uses OpenCV
            Haar cascade classifiers. Defaults to False.
        refine (bool, optional): When True, frames the histogram would skip but
            whose worst tile differs sharply from the reference are re-checked
            with a HOG or ORB descriptor, and saved if that check calls them
            distinct and the picture has stopped moving. This only ever adds
            frames, so the output is a superset of the unrefined run, though a
            refined frame can lag the change that caused it while an animation
            settles. Defaults to False.

    Returns:
        None
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    face_cascade, eye_cascade = (_load_eye_cascades() if open_eyes_only else (None, None))

    video_file_name = Path(video_path).stem
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        print("Error: Could not retrieve FPS.")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    if start_time >= duration:
        print(f"Error: start_time ({start_time:.1f}s) is beyond the video duration ({duration:.1f}s).")
        cap.release()
        return

    print(f"Video FPS: {fps} | Duration: {duration:.1f}s | Starting at: {start_time:.1f}s")

    # We want to check frames every 1 second
    frame_interval = int(fps)

    # Seek once to the start position, then walk the stream. Setting
    # CAP_PROP_POS_FRAMES per sample makes the decoder restart from the nearest
    # keyframe every time, which on inter-frame-coded video costs more than the
    # comparison it feeds. grab() advances without paying for the colour
    # conversion and copy that retrieve() does, so unsampled frames stay cheap.
    start_frame_idx = int(start_time * fps)
    if start_frame_idx > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame_idx)

    current_frame_idx = start_frame_idx
    next_sample_idx = start_frame_idx
    saved_count = 0
    last_saved_frame = None
    last_saved_timestamp = None
    skip_reference_frame = None
    skip_reference_timestamp = None
    # Derived data for the current reference frame, memoized on its timestamp so
    # a reference is only ever processed once no matter how many samples are
    # compared against it. Stage-1 data is built lazily - most runs never
    # escalate, and it is the expensive half.
    ref_hist_timestamp = None
    ref_hist = None
    ref_stage1_timestamp = None
    ref_thumbnail = None
    ref_use_hog = False
    ref_signature = None
    # Settling state, only maintained when refining.
    prev_thumbnail = None
    unsettled_streak = 0

    while True:
        if not cap.grab():
            break

        if current_frame_idx != next_sample_idx:
            current_frame_idx += 1
            continue

        ret, frame = cap.retrieve()
        if not ret:
            break

        timestamp = current_frame_idx / fps
        should_save = False
        # One 64px resize per sample, reused by both the guard and the settle
        # check. Skipped entirely when not refining.
        frame_thumbnail = _thumbnail(frame) if refine else None

        if last_saved_frame is None:
            should_save = True
            similarity = 0.0 # No previous frame
            print(f"[{timestamp:.1f}s] First frame → SAVE")
        else:
            # Determine reference frame
            # If we have a skip reference (from previous skip), use that
            # Otherwise use the last saved frame
            if skip_reference_frame is not None:
                reference_frame = skip_reference_frame
                ref_timestamp = skip_reference_timestamp
                ref_label = "skip_ref"
            else:
                reference_frame = last_saved_frame
                ref_timestamp = last_saved_timestamp
                ref_label = "last"

            if ref_hist_timestamp != ref_timestamp:
                ref_hist = _colour_histogram(reference_frame)
                ref_hist_timestamp = ref_timestamp

            similarity = cv2.compareHist(ref_hist, _colour_histogram(frame), cv2.HISTCMP_CORREL)

            if similarity < threshold:
                should_save = True
                print(f"[{timestamp:.1f}s] vs {ref_label}@{ref_timestamp:.1f}s | sim={similarity:.3f} → SAVE")
                # Clear skip reference when we save
                skip_reference_frame = None
                skip_reference_timestamp = None
                unsettled_streak = 0
            else:
                # The histogram wants to skip. Let the colour guard escalate the
                # cases it is known to be blind to, and only those.
                refine_saves = False
                refine_note = ""
                if refine:
                    if ref_stage1_timestamp != ref_timestamp:
                        ref_thumbnail = _thumbnail(reference_frame)
                        ref_use_hog = _flat_fraction(ref_thumbnail) >= _FLAT_FRACTION_CUTOFF
                        ref_signature = _stage1_signature(reference_frame, ref_use_hog)
                        ref_stage1_timestamp = ref_timestamp

                    delta = _colour_delta(ref_thumbnail, frame_thumbnail)
                    if delta >= _GUARD_DELTA_CUTOFF:
                        distinct = _stage1_is_distinct(
                            ref_signature, _stage1_signature(frame, ref_use_hog),
                            ref_use_hog, delta
                        )
                        verdict = "distinct" if distinct else "same"
                        refine_note = (
                            f" | delta={delta:.1f} "
                            f"{'hog' if ref_use_hog else 'orb'}={verdict}"
                        )
                        if distinct:
                            # Hold a distinct frame until the picture stops
                            # moving, so an animation emits its settled state
                            # once instead of a frame per step of the transition.
                            motion = (prev_thumbnail is not None and
                                      _colour_delta(prev_thumbnail, frame_thumbnail) >= _SETTLE_DELTA)
                            if not motion:
                                refine_saves = True
                                unsettled_streak = 0
                            elif unsettled_streak >= _SETTLE_MAX_WAIT:
                                refine_saves = True
                                unsettled_streak = 0
                                refine_note += " unsettled/forced"
                            else:
                                unsettled_streak += 1
                                refine_note += f" moving({unsettled_streak})"
                        else:
                            unsettled_streak = 0

                if refine_saves:
                    should_save = True
                    print(f"[{timestamp:.1f}s] vs {ref_label}@{ref_timestamp:.1f}s | sim={similarity:.3f}{refine_note} → SAVE")
                    skip_reference_frame = None
                    skip_reference_timestamp = None
                else:
                    print(f"[{timestamp:.1f}s] vs {ref_label}@{ref_timestamp:.1f}s | sim={similarity:.3f}{refine_note} → SKIP")
                    # When we skip, set the skip reference to the last saved frame
                    # so next comparison uses this same reference
                    skip_reference_frame = last_saved_frame
                    skip_reference_timestamp = last_saved_timestamp

        if should_save and open_eyes_only:
            if not has_open_eyes(frame, face_cascade, eye_cascade):
                print(f"[{timestamp:.1f}s] Open-eyes check failed → SKIP")
                should_save = False

        if should_save:
            output_filename = os.path.join(output_folder, f"{video_file_name}_frame_{timestamp:.1f}.jpg")
            cv2.imwrite(output_filename, frame)
            
            # Update last saved frame
            last_saved_frame = frame
            last_saved_timestamp = timestamp
            
            saved_count += 1

        prev_thumbnail = frame_thumbnail
        next_sample_idx += frame_interval
        current_frame_idx += 1

    cap.release()
    print(f"Done. Extracted {saved_count} frames.")