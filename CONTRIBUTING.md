# Contributing to Distant Frames

Thank you for your interest in contributing to Distant Frames! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Getting Started

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/distant-frames.git
   cd distant-frames
   ```

2. **Install dependencies:**
   ```bash
   uv sync --frozen
   ```

3. **Verify installation:**
   ```bash
   uv run distant-frames --help
   ```

## Development Workflow

### Making Changes

1. **Create a new branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** to the codebase

3. **Test your changes:**
   ```bash
   # Build the package
   uv build
   
   # Test with a sample video
   uv run distant-frames test_video.mp4
   ```

### Code Style

- Follow [PEP 8](https://pep8.org/) Python style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and concise

### Testing

Before submitting a pull request:

1. **Test the CLI:**
   ```bash
   uv run distant-frames path/to/test/video.mp4
   ```

2. **Verify the build:**
   ```bash
   uv build
   ```

3. **Test installation from built package:**
   ```bash
   uv pip install dist/*.whl
   distant-frames --help
   ```

## Submitting Changes

### Pull Request Process

1. **Update documentation** if you've made changes to:
   - Command-line interface
   - Configuration options
   - Core functionality

2. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Brief description of your changes"
   ```

3. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request** on GitHub:
   - Provide a clear title and description
   - Reference any related issues
   - Explain what changes you made and why

### Commit Message Guidelines

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

- Python version (`python --version`)
- Operating system
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Error messages or logs

### Feature Requests

When requesting features:

- Explain the use case
- Describe the desired behavior
- Provide examples if possible

## Release Process

Releases are managed by project maintainers. See [PUBLISHING.md](PUBLISHING.md) for details on the release workflow.

## Questions?

Feel free to open an issue for any questions about contributing!

## License

By contributing to Distant Frames, you agree that your contributions will be licensed under the GNU General Public License v3.0 or later.
