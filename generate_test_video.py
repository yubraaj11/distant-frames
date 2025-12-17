import cv2
import numpy as np

def create_test_video(filename, duration=5, fps=10):
    height, width = 480, 640
    # Define codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    # Generate frames
    for i in range(duration * fps):
        # Create a black image
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Change content every 2 seconds (so 0-2s same, 2-4s same, etc)
        # Actually let's make it:
        # 0s-1.5s: Red
        # 1.5s-3.0s: Red (Identical to previous, should be skipped)
        # 3.0s-4.0s: Blue (Different, should be kept)
        # 4.0s-5.0s: Blue (Identical, should be skipped)
        
        if i < 1.5 * fps:
            frame[:] = (0, 0, 255) # Red
            cv2.putText(frame, "Scene 1", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        elif i < 3.0 * fps:
            frame[:] = (0, 0, 255) # Still Red (Similar to Scene 1)
            cv2.putText(frame, "Scene 1 (Extended)", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            # Add small noise to test threshold not being 1.0
            noise = np.random.randint(0, 5, (height, width, 3), dtype=np.uint8)
            frame = cv2.add(frame, noise)
        elif i < 4.0 * fps:
            frame[:] = (255, 0, 0) # Blue
            cv2.putText(frame, "Scene 2", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        else:
            frame[:] = (255, 0, 0) # Blue
            cv2.putText(frame, "Scene 2 (Extended)", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        out.write(frame)
        
    out.release()
    print(f"Test video saved as {filename}")

if __name__ == "__main__":
    create_test_video("test_video.mp4")
