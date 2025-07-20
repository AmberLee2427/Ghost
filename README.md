# Ghost - AI Assistant That Haunts Your Devices

An intelligent AI assistant that provides consistent, context-aware interactions across Discord and Obsidian, with local memory management and RAG capabilities.

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

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built on the foundation of MyBMO (original by Longy2k)
- Uses txtai for RAG capabilities
- Inspired by the need for intelligent, cross-platform AI assistants
