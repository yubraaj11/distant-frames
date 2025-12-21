![PyPI - Version](https://img.shields.io/pypi/v/distant-frames)
![PyPI - Status](https://img.shields.io/pypi/status/distant-frames)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/distant-frames)
![GitHub License](https://img.shields.io/github/license/yubraaj11/distant-frames)

# Distant Frames

**Distant Frames** is a smart video frame extraction tool designed to capture distinct visual moments from video files. Instead of simply saving every Nth frame, it analyzes the visual similarity between consecutive potential frames and only saves those that are sufficiently different.

## 🚀 Features

- **Smart Deduplication**: Avoids saving redundant frames where the scene hasn't changed.
- **Histogram Correlation**: Uses HSV color space histogram comparison for robust similarity detection.
- **Configurable Threshold**: Fine-tune the sensitivity of frame dropping to suit your specific video content.
- **Efficient Processing**: Seeks directly to target timestamps (`CAP_PROP_POS_FRAMES`) for faster processing than frame-by-frame reading.

## 🛠️ Prerequisites

- **Python**: 3.12 or higher
- **Dependencies**: `opencv-python`

## 📦 Installation

### From PyPI (Recommended)

Install the latest stable release using pip:

```bash
pip install distant-frames

or 

uv add distant-frames
```

### From Source (Development)

For development or to use the latest unreleased features:

1. **Clone the repository:**
   ```bash
   git clone git@github.com:yubraaj11/distant-frames.git
   cd distant-frames
   ```

2. **Install Dependencies:**
   ```bash
   uv sync --frozen
   ```

## 💻 Usage

### Basic Command
Run the script by providing the path to your video file:

```bash
uv run distant_frames/cli.py path/to/your/video.mp4
```

### Options

| Argument | Description | Default |
|----------|-------------|---------|
| `video_path` | Path to the input video file (Required). | N/A |
| `--output` | Directory to save the extracted frames. | `extracted_frames` |
| `--threshold` | Similarity threshold (0.0 to 1.0). Frames with similarity **higher** than this value compared to the last saved frame will be **dropped**. | `0.65` |

### Examples

**Extract frames with default settings:**
```bash
uv run distant_frames/cli.py my_vacation.mp4
```

**Save to a custom folder with a stricter similarity check (fewer frames):**
```bash
uv run distant_frames/cli.py my_vacation.mp4 --output best_shots --threshold 0.95
```

**Save more frames (looser similarity check):**
```bash
uv run distant_frames/cli.py my_vacation.mp4 --output all_shots --threshold 0.6
```

## 🔍 How It Works

1. **Sampling**: The script checks one frame every second (based on the video's FPS).
2. **Comparison**: It compares the current candidate frame against the **last successfully saved frame**.
3. **Algorithm**: It converts frames to HSV color space and calculates Normalized Histogram Correlation.
4. **Decision**:
   - If similarity < `threshold`: **SAVE** (The scene has changed).
   - If similarity >= `threshold`: **SKIP** (The scene is too similar).

## 🧪 Testing

You can generate a test video to verify the functionality:

```bash
uv run generate_test_video.py
uv run main.py test_video.mp4
```

This will create a `test_video.mp4` with known scene changes and then extract frames from it, demonstrating the deduplication logic.
