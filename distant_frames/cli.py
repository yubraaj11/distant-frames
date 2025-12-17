import argparse
from distant_frames.core import extract_frames

def main():
    parser = argparse.ArgumentParser(description="Extract frames from video with similarity check.")
    parser.add_argument("video_path", help="Path to the input video file")
    parser.add_argument("--output", default="extracted_frames", help="Output directory for frames")
    parser.add_argument("--threshold", type=float, default=0.65, help="Similarity threshold (0-1). Higher value means stricter similarity check (more frames dropped).")
    
    args = parser.parse_args()
    
    extract_frames(args.video_path, args.output, args.threshold)

if __name__ == "__main__":
    main()
