# Publishing to PyPI

This document describes the process for publishing new releases of Distant Frames to PyPI.

## Prerequisites

### One-Time Setup

1. **PyPI Account**
   - Create an account at [pypi.org](https://pypi.org/account/register/)
   - Verify your email address

2. **API Token**
   - Go to [Account Settings → API tokens](https://pypi.org/manage/account/token/)
   - Click "Add API token"
   - Name: `distant-frames-github-actions`
   - Scope: Choose "Entire account" or limit to "distant-frames" project (after first release)
   - Copy the token (starts with `pypi-`)

3. **GitHub Secret**
   - Go to your repository on GitHub
   - Navigate to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: Paste your PyPI API token
   - Click "Add secret"

## Release Process

### 1. Prepare the Release

1. **Update version number** in `pyproject.toml`:
   ```toml
   [project]
   version = "X.Y.Z"
   ```

2. **Update CHANGELOG** (if you have one) with release notes

3. **Commit changes:**
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to X.Y.Z"
   git push origin main
   ```

### 2. Create and Push Tag

1. **Create a version tag:**
   ```bash
   git tag v0.1.0
   ```
   
   Follow [Semantic Versioning](https://semver.org/):
   - `vMAJOR.MINOR.PATCH` (e.g., `v1.2.3`)
   - MAJOR: Breaking changes
   - MINOR: New features (backward compatible)
   - PATCH: Bug fixes (backward compatible)

2. **Push the tag:**
   ```bash
   git push origin v0.1.0
   ```

### 3. Monitor the Release

1. **Watch GitHub Actions:**
   - Go to the "Actions" tab in your repository
   - Find the "Publish to PyPI" workflow run
   - Monitor the build and publish steps

2. **Verify on PyPI:**
   - Visit [pypi.org/project/distant-frames/](https://pypi.org/project/distant-frames/)
   - Confirm the new version is listed
   - Check that metadata displays correctly

3. **Test installation:**
   ```bash
   # In a fresh environment
   pip install distant-frames==X.Y.Z
   distant-frames --help
   ```

## Version Numbering Guidelines

- **0.1.0** - Initial release
- **0.1.1** - Bug fixes
- **0.2.0** - New features (backward compatible)
- **1.0.0** - First stable release
- **2.0.0** - Breaking changes

## Troubleshooting

### Build Fails

**Issue:** Package build fails in GitHub Actions

**Solution:**
- Check the Actions log for error messages
- Test the build locally: `uv build`
- Ensure `pyproject.toml` is valid
- Verify all dependencies are specified

### Upload Fails

**Issue:** "Invalid or non-existent authentication information"

**Solution:**
- Verify `PYPI_API_TOKEN` secret is set correctly in GitHub
- Ensure the token hasn't expired
- Check token scope includes the project

**Issue:** "File already exists"

**Solution:**
- You cannot re-upload the same version to PyPI
- Increment the version number in `pyproject.toml`
- Create a new tag with the updated version

### Package Not Found After Upload

**Issue:** `pip install distant-frames` fails immediately after release

**Solution:**
- Wait a few minutes for PyPI's CDN to update
- Check [pypi.org/project/distant-frames/](https://pypi.org/project/distant-frames/) to confirm upload
- Try with explicit version: `pip install distant-frames==X.Y.Z`

## Manual Publishing (Fallback)

If GitHub Actions fails, you can publish manually:

```bash
# Install publishing tools
pip install build twine

# Build the package
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

You'll be prompted for your PyPI username and password/token.

## Testing with TestPyPI

Before publishing to production PyPI, you can test with TestPyPI:

1. **Create TestPyPI account:** [test.pypi.org](https://test.pypi.org/)
2. **Generate API token** for TestPyPI
3. **Upload manually:**
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```
4. **Test installation:**
   ```bash
   pip install --index-url https://test.pypi.org/simple/ distant-frames
   ```

## Best Practices

- ✅ Test locally before creating a release tag
- ✅ Use semantic versioning consistently
- ✅ Keep a CHANGELOG to track changes
- ✅ Write release notes for significant updates
- ✅ Test installation in a clean environment
- ❌ Don't delete tags after publishing
- ❌ Don't reuse version numbers

## Questions?

If you encounter issues not covered here, please:
- Check the [GitHub Actions logs](../../actions)
- Review [PyPI's publishing guide](https://packaging.python.org/tutorials/packaging-projects/)
- Open an issue in the repository
