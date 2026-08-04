# Release Notes

## Version 0.4.0

### New Features

- **Refinement pass** (`--refine`): An opt-in second stage for frames the histogram would skip. When any one tile of an 8×8 grid over the picture differs sharply from the reference, the frame is re-checked with a descriptor and can be promoted to a save.

  This exists because the Hue/Saturation histogram has a measured blind spot: a slide-to-slide text change scores **1.000** — indistinguishable from an identical frame — because the changed text is too small a share of the picture to move a whole-frame average. On the reference deck that same pair scores **22.36** as a worst-tile difference against **0.27** for a true duplicate.

  The stage routes by content. `_flat_fraction()` measures how much of the picture sits in near-uniform regions; at or above `0.45` the frame is treated as graphic content and compared with a dense **HOG** descriptor under L2 distance, below it as camera footage and compared with **ORB** keypoints under Hamming distance. Keypoint detectors need texture that slides do not have, and the few keypoints a slide yields sit on the deck template — logo, rules, footer — which is identical across every slide, so ORB alone would report two different slides as a near-perfect match.

  A frame judged distinct is then held until the picture stops moving, so an animated slide emits its settled state once instead of one frame per step of the transition. On a 3-slide deck with titles flying in, this took the refined output from 9 frames to 4 while still recovering all 3 slides; the unrefined run finds only 1 of the 3.

### Improvements

- **Sequential decoding**: The extraction loop no longer seeks with `CAP_PROP_POS_FRAMES` once per sample. It seeks once to `--start`, then walks the stream with `grab()`, paying for a full decode only on sampled seconds. On inter-frame-coded video each seek restarts the decoder from the nearest keyframe, which costs more than the comparison it feeds.

  Measured on 120s of 720p, same content in two codecs: **5.09x** faster on H.264 with a 250-frame GOP (4.90s → 0.96s), 3.31x with `--start 37`, and 1.34x on short-GOP MPEG-4. Frame indices and decoded pixels are identical under both strategies.

- **Cached reference histogram**: A reference frame's histogram is computed once per segment rather than once per comparison. `calculate_similarity()` is unchanged and keeps its signature.

### Breaking Changes

- **The default threshold changed to `0.78`.** The CLI default moves from `0.75`, and `extract_frames()`'s default moves from `0.65`. A frame is kept when its similarity to the last kept frame falls *below* the threshold, so raising it means **more frames are kept by default**. Library callers who relied on the old `0.65` will see a larger shift than CLI users. Pass `--threshold` / `threshold=` explicitly to pin the previous behaviour.

  This value previously disagreed across the three places it is written — `core.py` said `0.65`, `cli.py` said `0.75`, and the README documented `0.65` — so the CLI and the library behaved differently from each other and from the docs. All three are now aligned.

### Fixes

- **`--threshold` help text stated the opposite of the actual behaviour.** It read "Higher values mean stricter deduplication (fewer frames saved)"; raising the threshold in fact keeps more frames. The CLI help, the `extract_frames()` docstring and the README options table now all state the direction explicitly.

### Compatibility

- **The similarity metric is unchanged**, and `--threshold` keeps its exact meaning. At an equal threshold a run is byte-identical to 0.3.2 — verified on stdout and on frame bytes — so the decoding and caching work above is a performance change only. The default *value* changed, as noted under Breaking Changes; that is the only reason default output differs.
- The refinement stage can only turn a skip into a save, never the reverse, so `--refine` output is always a superset of the same run without it.
- **Refined frames may lag the change that caused them.** Because a distinct frame is held until motion settles, a refined save can land one or two seconds after the transition. On the reference video the recovered slide moves from `t=80.0` to `t=81.0`. Frames saved by the histogram itself are unaffected and keep exact timestamps.

### Known Limitations

- **The ORB path is untested.** Across every sampled second of all three test videos the router chose HOG 161 times and ORB zero times, because all of that material is graphic content (flat fraction 0.83–1.00). The footage branch and its constants are implemented but have never executed against real camera footage.
- **Refinement is content-dependent, in the way `--threshold` already is.** There is no descriptor cutoff that classifies every case correctly: "an element moved within a busy slide" and "small text changed on a mostly-empty slide" are geometrically the same event. Measured with HOG/L2, the gap between the least-similar true duplicate and the most-similar true change is **−0.118**, and a sweep of 36 descriptor geometries found nothing usefully positive. This reproduces the same overlap previously measured for a blur-based metric (−0.116 to −0.029, never positive). The settling rule works around this temporally rather than solving it, which is why `--refine` is opt-in and off by default.
- **All refinement cutoffs are tuned on synthetic material**, not a labelled corpus. `_SETTLE_MAX_WAIT` in particular is a safety net chosen so that continuously animating content cannot lose a scene; the longest animation observed took 4 samples against a budget of 8.
- **The first sampled frame is always saved**, unconditionally and without a settle check. On a deck that opens mid-animation this frame can be caught before the content has arrived.

---

## Version 0.3.2

### Improvements

- **Temporal Consistency**: Replaced random UUIDs in filenames with video timestamps (e.g., `_frame_12.5.jpg`). This ensures that extracted frames are naturally sorted by their sequence in the video, making it easier to maintain temporal order.

---

## Version 0.3.1

### Fix

- **Local entry point**: Added `main.py` at the repo root so users who clone the repository can run the tool directly with `uv run main.py` without installing the package.

---

## Version 0.3.0

### New Features

- **Start timestamp** (`--start` / `-s`): Begin extraction from any point in the video by passing a timestamp in seconds. The video duration is validated upfront, and the startup log now shows duration and the effective start time.

- **Open-eyes filter** (`--open-eyes`): When enabled, only frames where at least one face with both eyes open is detected are saved. Detection uses a two-stage Haar cascade pipeline (face → eye ROI) and runs only on frames that have already passed the similarity check, so it adds no overhead on skipped frames.

- **Local Haar cascade classifiers**: Cascade XML files are now loaded from the project-local `haarcascade_classifiers/` directory (`haarcascade_frontalface_default.xml` and `haarcascade_eye.xml`) instead of the OpenCV bundle. No new dependencies are required.

### Usage Examples

**Start from 90 seconds in:**
```bash
distant-frames interview.mp4 -s 90
```

**Only keep frames with open eyes:**
```bash
distant-frames interview.mp4 --open-eyes -o key_frames
```

**Combine all options:**
```bash
distant-frames interview.mp4 -s 90 -t 0.80 --open-eyes -o key_frames
```

---

## Version 0.2.1

### Updated File Name

- **Concise Filenames**: Extracted frames now use a shortened 8-character UUID (e.g., `_frame_a1b2c3d4.jpg`) instead of the full 32-character UUID. This ensures uniqueness while keeping filenames cleaner and easier to manage.

## Version 0.2.0 

### 🎨 Enhanced CLI Interface

We've completely redesigned the command-line interface using **Typer** for a significantly improved user experience!

#### ✨ New Features

- **Rich Terminal Output**: Beautiful, formatted help text with tables and color-coded sections
- **Short Option Flags**: Added convenient shortcuts:
  - `-o` for `--output`
  - `-t` for `--threshold`
- **Automatic Validation**: Built-in input validation with helpful error messages
  - File existence checking before processing
  - Threshold range validation (0.0-1.0)
  - Readable file verification

#### 🔧 Improvements

- **Better Help Messages**: Clear, comprehensive help text with detailed parameter descriptions
- **Type Safety**: Full type hints for all CLI parameters with automatic validation
- **Enhanced Error Handling**: User-friendly error messages with suggestions and proper formatting
- **Cleaner Code**: More maintainable and declarative CLI implementation

#### 📦 Dependencies

- Added `typer>=0.9.0` for improved CLI functionality

#### 🎯 Usage Examples

**Basic usage:**
```bash
distant-frames video.mp4
```

**With custom output directory:**
```bash
distant-frames video.mp4 -o my_frames
```

**With custom threshold:**
```bash
distant-frames video.mp4 -t 0.8
```

**Combined options:**
```bash
distant-frames video.mp4 -o output_frames -t 0.7
```

**View help:**
```bash
distant-frames --help
```

#### 🐛 Bug Fixes

- Improved error messages when video file is not found
- Better validation for threshold parameter values

#### ⚠️ Breaking Changes

None - the CLI interface remains backward compatible with existing usage patterns.

---

## Version 0.1.2

### Features

- Smart frame extraction with similarity-based deduplication
- Fallback mechanism for gradual scene changes
- Verbose logging for debugging
- HSV-based histogram comparison for robust similarity detection

### Core Functionality

- Extract frames at 1-second intervals
- Skip similar frames based on configurable threshold
- Automatic output directory creation
- Detailed frame-by-frame logging
