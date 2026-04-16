# Release Notes

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
