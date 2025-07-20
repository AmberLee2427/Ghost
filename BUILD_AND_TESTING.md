# Ghost Build and Testing Instructions

This document provides step-by-step instructions for building, testing, and deploying the Ghost AI project.

## Prerequisites

### Required Software
- **Node.js** (v16 or higher)
- **Python** (3.11 or higher)
- **Git**
- **Obsidian** (for testing the plugin)

### Required Accounts
- **PyPI** account (for publishing the brain package)
- **GitHub** account (for repository access)

## Project Structure

```
Ghost/
├── brain/                    # Python brain server
│   ├── ghost_brain/         # Brain package source
│   ├── tests/               # Brain tests
│   ├── setup.py             # Brain package setup
│   └── requirements.txt     # Brain dependencies
├── src/                     # Obsidian plugin source
├── manifest.json            # Obsidian plugin manifest
├── package.json             # Node.js dependencies
└── README.md               # Project documentation
```

## Step 1: Build the Obsidian Plugin

### Navigate to Project Root
```bash
cd /path/to/Ghost
```

### Install Dependencies
```bash
npm install
```

### Build the Plugin
```bash
npm run build
```

This will create:
- `main.js` - Compiled plugin
- `styles.css` - Plugin styles
- `manifest.json` - Plugin manifest (updated with version)

### Verify Build
```bash
ls -la main.js manifest.json
```

## Step 2: Test the Brain Server

### Navigate to Brain Directory
```bash
cd brain
```

### Install Brain Package
```bash
pip install -e .
```

### Run Brain Tests
```bash
# Run all tests
pytest

# Run specific test suites
pytest test_environment_config.py
pytest test_cli.py

# Skip failing import test
pytest -k "not test_import_chatgpt_zip"

# Run with verbose output
pytest -v
```

### Test Brain Server
```bash
# Test CLI
ghost-brain --help
ghost-brain config
ghost-brain env-docs

# Start brain server
ghost-brain server --port 8000 --log-level debug

# Test health endpoint (in another terminal)
curl http://localhost:8000/health
```

## Step 3: Manual Plugin Installation

### Method 1: Symlink (Recommended for Development)
```bash
# Find your Obsidian plugins directory
# macOS: ~/Library/Application Support/obsidian/plugins/
# Windows: %APPDATA%\obsidian\plugins\
# Linux: ~/.config/obsidian/plugins/

# Create symlink
ln -s /path/to/Ghost ~/Library/Application\ Support/obsidian/plugins/ghost-ai
```

### Method 2: Copy Files
```bash
# Copy plugin files to Obsidian plugins directory
cp -r /path/to/Ghost ~/Library/Application\ Support/obsidian/plugins/ghost-ai/
```

### Method 3: ZIP Installation
```bash
# Create plugin ZIP
cd /path/to/Ghost
zip -r ghost-ai.zip main.js manifest.json styles.css

# Install via Obsidian:
# 1. Open Obsidian Settings
# 2. Go to Community Plugins
# 3. Turn off Safe mode
# 4. Click "Install plugin from file"
# 5. Select ghost-ai.zip
```

## Step 4: Configure Plugin in Obsidian

### Enable Plugin
1. Open Obsidian Settings
2. Go to Community Plugins
3. Find "Ghost AI" and enable it

### Configure Brain Server
1. Go to Ghost AI settings
2. Navigate to "Brain Server Settings"
3. Configure:
   - **Use Custom Brain Server**: Enable
   - **Brain Server URL**: `http://127.0.0.1:8000`
   - **Chat History Path**: Set to a folder with chat logs

### Test Connection
- Look for green status indicator
- If red, check brain server is running

## Step 5: Dry Run Testing

### Start Brain Server
```bash
cd brain
ghost-brain server --port 8000 --log-level debug
```

### Test in Obsidian
1. Open Ghost AI chat panel
2. Send a test message
3. Check brain server logs for API calls
4. Test ChatGPT import (if you have export files)

### Test ChatGPT Import
1. Get a ChatGPT export ZIP file
2. Use the import feature in Obsidian
3. Check brain server logs for import processing
4. Verify attachments are extracted and embedded

## Step 6: Publish to PyPI

### Prepare Brain Package
```bash
cd brain

# Update version in setup.py if needed
# Build distribution
python setup.py sdist bdist_wheel

# Check distribution
ls dist/
```

### Upload to PyPI
```bash
# Install twine if not installed
pip install twine

# Upload to PyPI
twine upload dist/*

# Or upload to test PyPI first
twine upload --repository testpypi dist/*
```

### Verify Upload
```bash
# Test installation from PyPI
pip install ghost-brain --upgrade
ghost-brain version
```

## Step 7: Git Operations

### Commit Changes
```bash
# Add all changes
git add .

# Commit with descriptive message
git commit -m "Add environment variables and CLI support

- Add comprehensive environment variable configuration
- Add CLI interface with argument parsing
- Add configuration management commands
- Update documentation and testing
- Fix known issues in AGENTS.md"

# Push to remote
git push origin main
```

### Create Release Tag
```bash
# Create and push tag
git tag v0.1.0
git push origin v0.1.0
```

## Troubleshooting

### Build Issues
```bash
# Clean and rebuild
rm -rf node_modules package-lock.json
npm install
npm run build

# Check TypeScript errors
npx tsc --noEmit
```

### Test Issues
```bash
# Run tests with more detail
pytest -v --tb=short

# Run specific test file
pytest tests/test_specific.py -v

# Debug failing test
pytest tests/test_specific.py -v -s
```

### Plugin Issues
```bash
# Check plugin logs in Obsidian
# Go to Settings → About → Open developer tools
# Check Console tab for errors

# Rebuild plugin
npm run build

# Restart Obsidian
```

### Brain Server Issues
```bash
# Check if port is in use
lsof -i :8000

# Test brain server directly
python -m ghost_brain.server

# Check configuration
ghost-brain config
```

## Known Issues

### ChatGPT Import Test Failure
- **Issue**: `test_import_chatgpt_zip.py` fails because no messages are imported
- **Status**: Under investigation
- **Workaround**: Skip test with `pytest -k "not test_import_chatgpt_zip"`
- **Next**: Debug during real Obsidian integration

### Plugin Installation
- **Issue**: Plugin not available on Community Plugins page
- **Status**: Manual installation required for testing
- **Next**: Submit to Community Plugins after testing

## Success Criteria

### Brain Server ✅
- [ ] All tests pass (except known import test)
- [ ] CLI works correctly
- [ ] Environment variables load properly
- [ ] Server starts and responds to health check
- [ ] Package uploads to PyPI successfully

### Obsidian Plugin ✅
- [ ] Plugin builds without errors
- [ ] Plugin installs manually in Obsidian
- [ ] Brain server settings work correctly
- [ ] Connection to brain server established
- [ ] Chat functionality works
- [ ] ChatGPT import works (if tested)

### Integration ✅
- [ ] End-to-end workflow functions
- [ ] Real ChatGPT exports import correctly
- [ ] Attachments are processed and embedded
- [ ] Memory and RAG features work

## Next Steps

1. **Complete dry run testing** with real Obsidian plugin
2. **Debug ChatGPT import** with real export files
3. **Submit plugin** to Obsidian Community Plugins
4. **Add .env file support** (Phase 3)
5. **Performance optimization** and monitoring 