# Ghost - AI Assistant That Haunts Your Devices

An intelligent AI assistant that provides consistent, context-aware interactions across Discord and Obsidian, with local memory management and RAG capabilities.

## ☕ Support Our Work

If Ghost helps you, consider supporting its development:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/nexusplugins)

**Suggested amounts:**
- **$5** - Fuel our coding sessions with caffeine ☕
- **$25** - Power our AI development tools 🤖
- **$75** - Supercharge our entire dev toolkit 🚀

*Your support helps us continue building useful tools and explore new ways of making your life easier.*

### Support the Original Creators

Ghost is built on the excellent work of these developers:

**Nexus AI Chat Importer** by Akim Sissaoui:
[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/nexusplugins)

**MyBMO (Original BMO)** by Longy2k:
<a href='https://ko-fi.com/K3K8PNYT8' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi1.png?v=3' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>

## Overview

Ghost consists of three modular components working together:

- **Obsidian Plugin**: Settings hub and credential manager
- **Shared Brain**: Python-based intelligence with memory and RAG
- **Discord Bot**: Communication layer for cross-device statefulness

## Features

### Obsidian Integration
- **Settings Management**: Centralized configuration for API keys, Discord tokens, and system prompts
- **Smart Chat UI**: Displays last 20 messages with intelligent context management (no manual `/save`/`/load`)
- **Credential Storage**: Secure storage of all authentication tokens
- **Brain Installer**: Manages Python dependencies and brain component updates
- **Configurable Brain Server**: Connect to brain servers anywhere - local, remote, cloud, or team servers
- **Mobile Support**: Connect mobile Obsidian to desktop brain servers

### Discord Bot
- **Cross-Device Statefulness**: Consistent memory across all your devices
- **Multiple Personalities**: Configurable bot personas and triggers
- **Advanced Memory**: Local SQLite database with conversation history and embeddings
- **Rich Interactions**: Support for threads, attachments, mentions, and reactions

### Shared Intelligence
- **RAG System**: Semantic search with citations using txtai
- **Local Memory**: SQLite database with FAISS similarity search
- **Unified LLM Interface**: Support for OpenAI, Google, and other models
- **Intelligent Context**: Automatic chunking and context management
- **Flexible Deployment**: Run brain server locally, on remote desktops, or in the cloud

## Installation

### Prerequisites
- Obsidian (for the plugin)
- Python 3.8+ (for the brain and Discord bot)
- Discord Bot Token (for cross-device functionality)

### Setup
1. Install the Obsidian plugin
2. Configure your API keys and Discord token in the plugin settings
3. The plugin will automatically install and manage the Python brain components
4. Start the Discord bot through the plugin interface

## Development

### Quick Start
For developers wanting to build and test the project:

```bash
# Clone the repository
git clone https://github.com/AmberLee2427/Ghost.git
cd Ghost

# Build the Obsidian plugin
npm install
npm run build

# Set up the brain server
cd brain
pip install -e .
./quick_start.sh
```

### Manual Plugin Installation
For testing the Obsidian plugin:

```bash
# Method 1: Symlink (recommended for development)
ln -s /path/to/Ghost ~/Library/Application\ Support/obsidian/plugins/ghost-ai

# Method 2: ZIP installation
cd /path/to/Ghost
zip -r ghost-ai.zip main.js manifest.json styles.css
# Then install via Obsidian: Settings → Community Plugins → Install from file
```

### Testing
```bash
# Test brain server
cd brain
pytest -k "not test_import_chatgpt_zip"  # Skip known failing test

# Test CLI
ghost-brain --help
ghost-brain config
ghost-brain env-docs

# Test brain server
ghost-brain server --port 8000 --log-level debug
```

### PyPI Release
```bash
cd brain
./release_to_pypi.sh
```

📖 **Detailed Instructions**: See [BUILD_AND_TESTING.md](BUILD_AND_TESTING.md) for comprehensive build and testing instructions.

## Automated Releases

The project uses GitHub Actions for automated releases:

### Prerequisites
1. **PyPI API Token**: Create one at [PyPI Account Settings](https://pypi.org/manage/account/)
2. **GitHub Secret**: Add `PYPI_API_TOKEN` to your repository secrets

### Release Process
1. Update version in `brain/setup.py`
2. Commit and push changes
3. Create and push a version tag: `git tag v0.1.2 && git push origin v0.1.2`
4. GitHub Actions automatically:
   - Runs tests
   - Builds and uploads brain package to PyPI
   - Verifies installation

📖 **Complete Guide**: See [RELEASE_GUIDE.md](RELEASE_GUIDE.md) for detailed release instructions.

## Configuration

### API Keys
- **OpenAI**: For GPT models
- **Google**: For Gemini models  
- **Discord**: For cross-device bot functionality

### Brain Server Settings
- **Local Mode**: Default localhost:8000 configuration
- **Custom Mode**: Connect to any brain server URL (cloud, remote desktop, team server)
- **Mobile Support**: Use desktop IP address in mobile settings
- **Team Sharing**: Share one brain server across multiple team members

### System Prompts
- Configure custom system prompts for different use cases
- Set personality and behavior parameters
- Define conversation styles and expertise areas

## Usage

### In Obsidian
1. Open the Ghost panel in the sidebar
2. Start chatting - context is managed automatically
3. No need for `/save` or `/load` commands
4. Chat history is intelligently maintained
5. Brain server status indicator shows connection health

### On Discord
1. Mention the bot or reply to its messages
2. Use keyword triggers for specific interactions
3. Bot maintains context across conversations
4. Access the same intelligence as Obsidian

### Mobile Setup
1. Install brain on desktop: `python -m pip install ghost-brain`
2. Start brain server: `python -m ghost_brain.server`
3. Find desktop IP: `ifconfig` (Mac/Linux) or `ipconfig` (Windows)
4. In mobile Obsidian settings, use: `http://YOUR_DESKTOP_IP:8000`

### Cloud Deployment
1. Deploy brain to Railway/Heroku/etc.
2. Get your deployment URL
3. In Obsidian settings, use: `https://your-deployment-url.com`

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Obsidian Plugin                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Settings UI   │  │   Chat UI       │  │  Brain       │ │
│  │   (Credentials) │  │   (Frontend     │  │  Installer   │ │
│  │   • API Keys    │  │   Only)         │  │  • txtai     │ │
│  │   • Discord     │  │   • Last 20     │  │  • Memory    │ │
│  │   • Brain       │  │   • No /save    │  │  • Discord   │ │
│  │   • System      │  │   • Smart       │  │  • Bot       │ │
│  │   • Prompts     │  │   Context       │  └──────────────┘ │
│  └─────────────────┘  └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌─────────────────┐
                    │   Shared Brain  │
                    │   (Python)      │
                    │   • txtai RAG   │
                    │   • Citations   │
                    │   • Memory DB   │
                    │   • LLM Handler │
                    │   • HTTP API    │
                    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────┐
                    │   Discord Bot   │
                    │   (Background)  │
                    └─────────────────┘
```

## Development Status

### Phase 1: Foundation ✅
- [x] Discord bot with memory management
- [x] txtai reference implementation
- [x] Basic Obsidian plugin structure

### Phase 2: Cleanup and Modularization ✅
- [x] Strip MyBMO dependencies from plugin
- [x] Extract brain into standalone module
- [x] Update documentation
- [x] Create credential bridge

### Phase 3: Integration ✅
- [x] Smart context management
- [x] Brain installer
- [x] Chat UI redesign
- [x] txtai integration
- [x] Configurable brain server settings
- [x] Mobile support

### Phase 4: Enhancement 🚀
- [ ] Agentic file editing capabilities
- [ ] Google Calendar/Gmail integration
- [ ] Advanced RAG features
- [ ] Brain server authentication
- [ ] Automatic brain server discovery

## Technical Details

- **Obsidian Plugin**: TypeScript, Obsidian API
- **Shared Brain**: Python, SQLite, txtai, sentence-transformers
- **Discord Bot**: Python, discord.py
- **RAG Engine**: txtai with local embeddings
- **Memory**: SQLite with FAISS for similarity search
- **Brain Server**: FastAPI with configurable endpoints

## Contributing

This project is in active development. Contributions are welcome!

## Credits

### Chat History Integration
Ghost's chat history embedding feature is built on the excellent work of:

**[Nexus AI Chat Importer](https://github.com/superkikim/nexus-ai-chat-importer)** by [Akim Sissaoui](https://ko-fi.com/nexusplugins)

This Obsidian plugin provides the foundation for importing and organizing ChatGPT conversations. Ghost extends this capability by embedding these conversations into semantic memory for intelligent search and context retrieval.

### Foundation
Ghost is built on the foundation of:

**[MyBMO](https://github.com/NoguchiShigeki/MyBMO)** by NoguchiShigeki

A repackaged version of the original BMO chatbot with enhancements. We forked from this version and significantly refactored it into Ghost.

**Original BMO**: **[obsidian-bmo-chatbot](https://github.com/longy2k/obsidian-bmo-chatbot)** by [Longy2k](https://ko-fi.com/K3K8PNYT8)

The original BMO chatbot plugin for Obsidian that started it all.

### Other Acknowledgments
- Uses txtai for RAG capabilities
- Inspired by the need for intelligent, cross-platform AI assistants

## License

MIT License - see [LICENSE](https://github.com/AmberLee2427/Ghost/blob/main/LICENSE) file for details.

* [MyBMO License](https://github.com/NoguchiShigeki/MyBMO/blob/main/LICENSE)
* [obsidian-bmo-chatbot license](https://github.com/longy2k/obsidian-bmo-chatbot/blob/main/LICENSE)
* [nexus-ai-chat-importer license](https://github.com/Superkikim/nexus-ai-chat-importer/blob/1.1.0/LICENSE.md)