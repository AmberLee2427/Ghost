# Project Ghost

We are creating an AI assistant that feels like it haunts your devices. We are piggybacking on existing frameworks. A discord bot for statefullness across devices. Obsidian plugins to leverage existing architecture around chat log storage. Obsidian BMO chat for better workflow integration. At some point, in would be nice to expand to Google Calendar and gmail integration.

ChatGPT has an export chat log function and there exist Obsidian plugins (e.g. nexus-ai-chat-importer) for converting zipped chat-log archives into markdown records (example in `ref/chatlogs/`).

We will utilize `txtai` (codebase in `ref/txtai/`, for reference) to perform the chat log embeddings (using local models) and RAG, for consistent, cross-platform recall.

The main repo is a clone of MyBMO. An AI chatbot plugin for obsidian. We will be heavily altering it.

The inspiration for the discord bot is in `src/discord/` this is a clone of a repo of mine for a project with two simultaneously run discord bots.

## Development Plan

### Step 1: The path forward

The obsidian chatbot and our bot "brain" should interact modularly. Why?

#### 1. Different Interaction Patterns

* Discord: Real-time, conversational, multi-user, with rich context (mentions, threads, attachments)
* Obsidian: Note-focused, single-user, document-centric, with markdown rendering
* These are fundamentally different UX paradigms that benefit from specialized frontends

#### 2. The Discord Bot is Already Sophisticated

The Discord implementation has:

* Advanced memory management with SQLite
* Chunking and embedding logic
* Multi-bot personality system
* Structured reasoning responses
* Background memory processing

This is a solid foundation that shouldn't be compromised by Obsidian's constraints.

#### 3. Obsidian Plugin Has Different Strengths

The MyBMO plugin excels at:

* Note integration and markdown rendering
* File system operations
* Profile/prompt management
* Chat history as notes
* Editor commands and workflows

#### Recommended Architecture

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

**Key Benefits:**

* **Settings Centralization:** All credentials, API keys, system prompts in one Obsidian interface
* **Smart Context:** No more `/save`/`/load` - just intelligent context management
* **`txtai` Citations:** Proper RAG with source attribution
* **Agentic Dreams:** Future file editing capabilities
* **Clean Separation:** Plugin = UI/Config, Brain = Intelligence, Discord = Communication

#### Shared Components

* **Memory Database:** SQLite with your existing schema
* **Embedding Engine:** `txtai` for RAG capabilities
* **LLM Handler:** Unified API for different models
* **Chunking Logic:** Your existing conversation processing

#### Platform-Specific

* **Discord:** Real-time messaging, bot personalities, Discord API
* **Obsidian:** Note integration, markdown rendering, file operations

This approach gives you:

* **Consistency:** Same memory and reasoning across platforms
* **Flexibility:** Each frontend optimized for its environment
* **Maintainability:** Clear separation of concerns
* **Future-Proofing:** Easy to add new platforms (web UI, mobile, etc.)

### Step 2: Make it make sense

We want to clean up al the documentation and comments to reflect the planned refactorings.

* Remove all instances of the second bot
* Move all environment variables to be Obsidian plugin settings.
* Remove all old repo naming references
* Re-write documentations such as the README.md, respecting the MyBMO license.

### Step 3: Implementation

1. **Strip MyBMO:** Remove all the chat logic, keep only settings UI and basic chat display
2. **Brain Installer:** Plugin handles installing/updating the Python brain components
3. **Credential Bridge:** Plugin stores settings, brain reads them
4. **Context API:** Chat UI just displays, brain handles all context management
5. **Discord Integration:** Plugin can start/stop Discord bot, manage its config

#### Immediate Next Steps

1. **Clean up the plugin:** Remove MyBMO branding and chat logic
2. **Extract brain components:** Move your Discord bot's intelligence into a standalone module
3. **Create the bridge:** Simple API between plugin settings and brain
4. **Implement smart context:** Replace `/save`/`/load` with intelligent context management
