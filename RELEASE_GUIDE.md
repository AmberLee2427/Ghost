# Ghost Brain Release Guide

This guide explains how to use the automated GitHub Actions workflow to release the Ghost Brain package to PyPI.

## Overview

The brain package uses GitHub Actions to automatically:
- **Test** code on every push and pull request
- **Release to PyPI** when you create a version tag for the brain package

## Prerequisites

### 1. PyPI API Token
You need to create a PyPI API token and add it to GitHub secrets:

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Click "Add API token"
3. Give it a name like "Ghost Brain Release"
4. Select "Entire account (all projects)"
5. Copy the token (starts with `pypi-`)

### 2. Add GitHub Secret
1. Go to the **brain repository** (not the main Ghost repository)
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Name: `PYPI_API_TOKEN`
5. Value: Your PyPI token (e.g., `pypi-abc123...`)

## Release Process

### Step 1: Update Version
Update the version in `setup.py`:

```python
setup(
    name="ghost-brain",
    version="0.1.2",  # Increment this
    # ... rest of setup
)
```

### Step 2: Commit and Push
```bash
git add .
git commit -m "Release v0.1.2 - Add new features"
git push origin main
```

### Step 3: Create Release Tag
```bash
# Create and push the tag
git tag v0.1.2
git push origin v0.1.2
```

### Step 4: Monitor Workflow
The tag push will automatically trigger:
1. **Test workflow** - Runs all tests
2. **Release workflow** - Builds and uploads brain package to PyPI

You can monitor progress at: `https://github.com/your-brain-repo/actions`

## Workflow Details

### Test Workflow (`test.yml`)
**Triggers**: Push to main, Pull requests
**What it does**:
- Runs brain tests (skips known failing import test)
- Tests CLI functionality
- Tests brain server startup

### Release Workflow (`release.yml`)
**Triggers**: Version tags (v*)
**What it does**:
- Runs tests
- Builds Python package
- Uploads to PyPI
- Verifies installation

## Release Artifacts

After a successful release, you'll have:

### PyPI Package
- **Package**: `ghost-brain` available on PyPI
- **Install**: `pip install ghost-brain --upgrade`
- **Test**: `ghost-brain version`

## Manual Release (Fallback)

If the automated workflow fails, you can release manually:

```bash
# Build and upload to PyPI
python setup.py sdist bdist_wheel
twine upload dist/*

# Verify installation
pip install ghost-brain --upgrade
ghost-brain version
```

## Troubleshooting

### Workflow Fails
1. Check the Actions tab for error details
2. Common issues:
   - Missing PyPI token secret
   - Test failures
   - Build errors

### PyPI Upload Fails
1. Verify PyPI token is correct
2. Check if version already exists (increment version)
3. Ensure package name is unique

## Version Management

### Semantic Versioning
Use semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Examples
- `v0.1.0` - Initial release
- `v0.1.1` - Bug fixes
- `v0.2.0` - New features
- `v1.0.0` - Stable release

## Best Practices

### Before Releasing
1. ✅ All tests pass
2. ✅ Documentation updated
3. ✅ Version incremented
4. ✅ Changelog updated (if applicable)

### Release Checklist
- [ ] Update version in `setup.py`
- [ ] Commit all changes
- [ ] Push to main branch
- [ ] Create and push version tag
- [ ] Monitor GitHub Actions
- [ ] Verify PyPI upload
- [ ] Test installation: `pip install ghost-brain --upgrade`
- [ ] Update release notes if needed

### After Release
- [ ] Test the new version
- [ ] Update any deployment scripts
- [ ] Notify users of new features
- [ ] Monitor for any issues

## Security Notes

- **PyPI Token**: Keep your PyPI API token secure
- **GitHub Secrets**: Never commit secrets to the repository
- **Token Rotation**: Rotate PyPI tokens periodically
- **Access Control**: Limit who can create release tags

## Support

If you encounter issues with the release process:

1. Check the [GitHub Actions documentation](https://docs.github.com/en/actions)
2. Review the workflow files in `.github/workflows/`
3. Check PyPI documentation for upload issues
4. Create an issue in the repository for persistent problems 