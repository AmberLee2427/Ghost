# Project Ghost

We are creating an AI assistant that feels like it haunts your devices. The system consists of three modular components:

1. **Obsidian Plugin** - Settings hub and credential manager
2. **Shared Brain** - Python-based intelligence with memory and RAG
3. **Discord Bot** - Communication layer for cross-device statefulness

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Obsidian Plugin                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Settings UI   │  │   Chat UI       │  │  Brain       │ │
│  │   (Credentials) │  │   (Frontend     │  │  Installer   │ │
│  │   • API Keys    │  │   Only)         │  │  • txtai     │ │
│  │   • Discord     │  │   • Last 20     │  │  • Memory    │ │
│  │   • System      │  │   • No /save    │  │  • Discord   │ │
│  │   • Prompts     │  │   • Smart       │  │  • Bot       │ │
│  └─────────────────┘  │   Context       │  └──────────────┘ │
│                       └─────────────────┘                   │
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
                    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────┐
                    │   Discord Bot   │
                    │   (Background)  │
                    └─────────────────┘
```

## Component Responsibilities

### Obsidian Plugin (TypeScript)
- **Settings Management**: API keys, Discord tokens, system prompts, model preferences
- **Credential Storage**: Secure storage of all authentication tokens
- **Chat UI**: Simple frontend displaying last 20 messages (no `/save`/`/load` commands)
- **Brain Installer**: Manages installation/updates of Python brain components
- **File Integration**: Future agentic capabilities for editing current notes

### Shared Brain (Python)
- **Memory Management**: SQLite database with conversation history and embeddings
- **RAG System**: Using `txtai` for semantic search with citations
- **LLM Handler**: Unified interface for OpenAI, Google, and other models
- **Context Processing**: Intelligent chunking and context management
- **Reasoning Engine**: Structured responses with internal reasoning

### Discord Bot (Python)
- **Communication**: Real-time messaging and cross-device statefulness
- **Personality System**: Multiple bot personas and triggers
- **Discord Integration**: Threads, attachments, mentions, reactions

## Development Plan

### Phase 1: Foundation (Current)
- [x] Discord bot with memory management (in `src/discord/`)
- [x] txtai reference implementation (in `ref/txtai/`)
- [x] Basic Obsidian plugin structure (forked from MyBMO)

### Phase 2: Cleanup and Modularization
- [ ] **Strip MyBMO**: Remove chat logic from Obsidian plugin, keep only settings UI
- [ ] **Extract Brain**: Move Discord bot intelligence into standalone Python module
- [ ] **Update Documentation**: Clean up README and remove MyBMO branding
- [ ] **Credential Bridge**: Create API for plugin settings to communicate with brain

### Phase 3: Integration
- [ ] **Smart Context**: Replace `/save`/`/load` with intelligent context management
- [ ] **Brain Installer**: Plugin handles Python dependencies and brain updates
- [ ] **Chat UI Redesign**: Simple display of last 20 messages with smart context
- [ ] **txtai Integration**: Implement RAG with citations in brain

### Phase 4: Enhancement
- [ ] **Agentic Capabilities**: File editing and note manipulation
- [ ] **Google Calendar/Gmail Integration**: Expand cross-platform capabilities
- [ ] **Advanced RAG**: Enhanced semantic search and memory retrieval

## Key Design Principles

1. **Modularity**: Each component has a single responsibility
2. **Smart Context**: No manual context management - intelligence handles it
3. **Citations**: All RAG responses include source attribution
4. **Cross-Platform**: Consistent experience across Discord and Obsidian
5. **Extensible**: Easy to add new platforms (web UI, mobile, etc.)

## Technical Stack

- **Obsidian Plugin**: TypeScript, Obsidian API
- **Shared Brain**: Python, SQLite, txtai, sentence-transformers
- **Discord Bot**: Python, discord.py
- **RAG Engine**: txtai with local embeddings
- **Memory**: SQLite with FAISS for similarity search

## Notes for Future Development

- The current Discord bot in `src/discord/` contains the most advanced implementation
- The `ref/txtai/` directory contains the reference implementation for RAG capabilities
- The Obsidian plugin needs significant cleanup to remove MyBMO dependencies
- Consider using a local API (HTTP or socket) for plugin-brain communication
- Future: Consider adding web UI and mobile app components

**Planned repo structure/workflow:**

```
Ghost Repo/
├── src/                    # Plugin code
├── brain/                  # Brain package (separate .git)
│   ├── .git/              # Brain's own git repo
│   ├── setup.py           # Brain package config
│   ├── ghost_brain/       # Brain source code
│   └── requirements.txt   # Python dependencies
└── README.md 
```
