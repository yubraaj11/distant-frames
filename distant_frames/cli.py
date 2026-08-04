import typer
from pathlib import Path
from typing_extensions import Annotated
from distant_frames.core import extract_frames

app = typer.Typer(
    help="Smart video frame extraction tool with similarity-based deduplication.",
    add_completion=False,
)

@app.command()
def main(
    video_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the input video file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        )
    ],
    output: Annotated[
        str,
        typer.Option(
            "--output", "-o",
            help="Output directory for extracted frames"
        )
    ] = "extracted_frames",
    threshold: Annotated[
        float,
        typer.Option(
            "--threshold", "-t",
            min=0.0,
            max=1.0,
            help="Similarity threshold (0.0-1.0). A frame is kept when its similarity to the last "
                 "kept frame falls below this value, so raising it keeps MORE frames, not fewer."
        )
    ] = 0.78,
    start_time: Annotated[
        float,
        typer.Option(
            "--start", "-s",
            min=0.0,
            help="Start extraction from this timestamp (in seconds). Defaults to 0 (beginning of video)."
        )
    ] = 0.0,
    open_eyes_only: Annotated[
        bool,
        typer.Option(
            "--open-eyes",
            help="Only save frames where at least one face with both eyes open is detected."
        )
    ] = False,
    refine: Annotated[
        bool,
        typer.Option(
            "--refine",
            help="Re-check frames the histogram would skip with a HOG/ORB descriptor when any "
                 "region of the picture changes sharply. Catches title/text changes on slides that "
                 "the histogram scores as identical. Only ever adds frames."
        )
    ] = False,
):
    """
    Extract distinct frames from a video file based on visual similarity.

    The tool samples the video at 1-second intervals and compares consecutive frames.
    Frames that are too similar to previously saved frames are automatically skipped.
    """
    extract_frames(str(video_path), output, threshold, start_time, open_eyes_only, refine)

if __name__ == "__main__":
    app()
