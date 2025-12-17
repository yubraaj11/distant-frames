import cv2
import os

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
    # Convert to HSV for better color handling, or Gray if color doesn't matter much.
    # HSV is generally more robust to lighting changes than BGR.
    hsv1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2HSV)
    hsv2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2HSV)

    # Calculate histograms
    # Channels 0 and 1 (Hue and Saturation) are usually enough
    hist1 = cv2.calcHist([hsv1], [0, 1], None, [180, 256], [0, 180, 0, 256])
    hist2 = cv2.calcHist([hsv2], [0, 1], None, [180, 256], [0, 180, 0, 256])

    # Normalize histograms
    cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
    cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)

    # Compare histograms
    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    return similarity

def extract_frames(video_path, output_folder, threshold=0.9):
    """Extracts distinct frames from a video file based on visual similarity.

    The function samples the video at 1-second intervals. It compares the current
    frame with the last saved frame. If the similarity score is below the
    specified threshold, the frame is considered distinct and saved.
    
    If a frame is skipped (similar to the last saved frame), the next comparison
    will be performed against the *previous* saved frame (if available) to ensure
    robustness against gradual changes or local similarities.

    Args:
        video_path (str): Path to the input video file.
        output_folder (str): Directory where extracted frames will be saved.
            The directory will be created if it does not exist.
        threshold (float, optional): Similarity threshold (0.0 to 1.0).
            Frames with similarity higher than this value regarding the last
            saved frame will be dropped. Higher values mean stricter
            deduplication (fewer frames saved). Defaults to 0.9.

    Returns:
        None
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        print("Error: Could not retrieve FPS.")
        return

    print(f"Video FPS: {fps}")
    
    # We want to check frames every 1 second
    frame_interval = int(fps)
    
    current_frame_idx = 0
    saved_count = 0
    last_saved_frame = None
    prev_saved_frame = None
    force_fallback_to_prev = False

    while True:
        # Set position to the next second
        # Note: Setting pos_frames is faster than reading every frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_idx)
        
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = current_frame_idx / fps
        should_save = False

        if last_saved_frame is None:
            should_save = True
            similarity = 0.0 # No previous frame
        else:
            # Determine reference frame
            reference_frame = last_saved_frame
            if force_fallback_to_prev and prev_saved_frame is not None:
                reference_frame = prev_saved_frame
                # We used fallback, so reset the flag for the next check 
                # (unless we skip again, which re-sets it below)
                force_fallback_to_prev = False 

            similarity = calculate_similarity(reference_frame, frame)
            if similarity < threshold:
                should_save = True
            else:
                print(f"Skipping frame at {timestamp:.2f}s (Similarity: {similarity:.4f})")
                force_fallback_to_prev = True

        if should_save:
            output_filename = os.path.join(output_folder, f"frame_{timestamp:.2f}.jpg")
            cv2.imwrite(output_filename, frame)
            
            # Update history
            prev_saved_frame = last_saved_frame
            last_saved_frame = frame
            
            # Reset fallback flag because we just saved a new distinct frame
            force_fallback_to_prev = False
            
            saved_count += 1
            print(f"Saved {output_filename} (Similarity: {similarity:.4f})")

        current_frame_idx += frame_interval

    cap.release()
    print(f"Done. Extracted {saved_count} frames.")
