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
            help="Similarity threshold (0.0-1.0). Higher values mean stricter deduplication (fewer frames saved)."
        )
    ] = 0.65,
):
    """
    Extract distinct frames from a video file based on visual similarity.
    
    The tool samples the video at 1-second intervals and compares consecutive frames.
    Frames that are too similar to previously saved frames are automatically skipped.
    """
    extract_frames(str(video_path), output, threshold)

if __name__ == "__main__":
    app()
