![PyPI - Version](https://img.shields.io/pypi/v/distant-frames)
![PyPI - Status](https://img.shields.io/pypi/status/distant-frames)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/distant-frames)
![PyPI - Downloads](https://img.shields.io/pypi/dm/distant-frames)
![GitHub License](https://img.shields.io/github/license/yubraaj11/distant-frames)

# Distant Frames

**Distant Frames** is a smart video frame extraction tool designed to capture distinct visual moments from video files. Instead of simply saving every Nth frame, it analyzes the visual similarity between consecutive potential frames and only saves those that are sufficiently different.

## 🚀 Features

- **Smart Deduplication**: Avoids saving redundant frames where the scene hasn't changed.
- **Histogram Correlation**: Uses HSV color space histogram comparison for robust similarity detection.
- **Configurable Threshold**: Fine-tune the sensitivity of frame dropping to suit your specific video content.
- **Efficient Processing**: Seeks directly to target timestamps (`CAP_PROP_POS_FRAMES`) for faster processing than frame-by-frame reading.
- **Custom Start Time**: Begin extraction from any point in the video using a timestamp in seconds.
- **Open Eyes Filter**: Optionally keep only frames where at least one face with both eyes open is detected, using local Haar cascade classifiers.

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

### From Source (Local)

Clone the repo and run directly without installing the package:

1. **Clone the repository:**
   ```bash
   git clone git@github.com:yubraaj11/distant-frames.git
   cd distant-frames
   ```

2. **Install dependencies:**
   ```bash
   uv sync --frozen
   ```

3. **Run via `main.py`:**
   ```bash
   uv run main.py path/to/video.mp4 -o output_dir -t 0.78
   ```

## 💻 Usage

### Installed package

```bash
distant-frames path/to/video.mp4 -o path/to/output -t 0.78
```

### Cloned repo (no install)

```bash
uv run main.py path/to/video.mp4 -o path/to/output -t 0.78
```

### Options

| Argument | Description | Default |
|----------|-------------|---------|
| `video_path` | Path to the input video file (Required). | N/A |
| `--output`, `-o` | Directory to save the extracted frames. | `extracted_frames` |
| `--threshold`, `-t` | Similarity score threshold (0.0 to 1.0). Frames with a score **higher** than this value are discarded, so raising it keeps **more** frames. | `0.78` |
| `--start`, `-s` | Timestamp in seconds to begin extraction from. | `0.0` |
| `--open-eyes` | When set, only saves frames where at least one face with both eyes open is detected. | Off |
| `--refine` | When set, frames the histogram would skip are re-checked with a HOG or ORB descriptor if any region of the picture changed sharply. Catches title and text changes on slides, which the histogram scores as identical. Waits for animation to settle before saving, so refined frames may lag the change by a second or two. Only ever adds frames. | Off |

### Examples

**Extract frames with default settings:**
```bash
distant-frames my_vacation.mp4
```

**Save to a custom folder with a stricter similarity check:**
```bash
distant-frames my_vacation.mp4 -o best_shots -t 0.95
```

**Start extraction from a specific timestamp (e.g. 1 minute 30 seconds in):**
```bash
distant-frames interview.mp4 -s 90
```

**Only keep frames where a person's eyes are open:**
```bash
distant-frames interview.mp4 --open-eyes -o key_frames
```

**Combine all options:**
```bash
distant-frames interview.mp4 -s 90 -t 0.80 --open-eyes -o key_frames
```

## 🔍 How It Works

1. **Sampling**: The script checks one frame every second (based on the video's FPS), starting from `--start` if provided.
2. **Comparison**: It compares the current candidate frame against the **last successfully saved frame**.
3. **Algorithm**: It converts frames to HSV color space and calculates Normalized Histogram Correlation.
4. **Decision**:
   - If similarity < `threshold`: candidate for saving.
   - If similarity >= `threshold`: **SKIP** (The scene is too similar).
5. **Refinement** *(optional)*: If `--refine` is set, a frame the histogram wants to skip gets a second look when the worst 1/64 tile of the picture changed sharply. A dense HOG descriptor (flat, graphic content) or ORB keypoints (textured footage) then decides, and can turn the skip into a save. This catches a title changing on an otherwise static slide, which alters too little of the picture to move a whole-frame histogram. A frame judged distinct is then held until the picture stops moving, so an animated slide emits its settled state once rather than one frame per step of the transition — which means a refined save can land a second or two after the change that caused it.
6. **Open Eyes Filter** *(optional)*: If `--open-eyes` is set, a candidate frame is only saved if a face with two open eyes is detected using Haar cascade classifiers.

## 🧪 Testing

You can generate a test video to verify the functionality:

```bash
uv run generate_test_video.py
uv run main.py test_video.mp4
```

This will create a `test_video.mp4` with known scene changes and then extract frames from it, demonstrating the deduplication logic.
