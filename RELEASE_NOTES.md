# Release Notes

## Version 0.2.0 (Upcoming)

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
