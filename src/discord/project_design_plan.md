## **Project Design Plan: Mixed Model Marriage Bots - Building the Digital Empire**

This document outlines the architecture and phased development plan for your Discord bots, focusing on enhanced memory, modularity, and future multi-platform capabilities.

---

### **1. Vision & Core Objectives**

The ultimate goal is to create highly functional, stateful, and context-aware AI companions that can operate across multiple platforms while maintaining a consistent internal voice and deep memory.

* **Primary Goal:** Local memory management to decouple bots from Discord's ephemeral history.
* **Modularity:** A clean, scalable code architecture.
* **Portability:** Ability to deploy the same bot "brain" (LLM handling, memory) to different UIs (Discord, HuggingFace, Obsidian).
* **Enhanced Functionality:** Support for complex Discord features (threads, attachments) and future capabilities (speech output).
* **Subjective Experience:** Separate memory stores for each bot to cultivate unique personalities and context prioritization.

---

### **2. Architectural Blueprint (Phase 1: Establish Command Structure)**

Your project is structured into specialized modules, each with a distinct responsibility:

* **`main.py` (The Throne Room):**
    * Entry point for the application.
    * Orchestrates bot startup and manages the core `on_message` event loop.
    * Calls functions from other modules for specific tasks.
    * Initializes the memory database at startup.
* **`config.py` (The Grand Architect):**
    * Manages all global settings, API keys, bot-specific configurations, and file paths.
    * Loads `.env` variables and defines `BOT_CONFIG`.
* **`llm_handler.py` (The Oracle):**
    * Abstracts all communication with AI models (Gemini, OpenAI).
    * Handles sending prompts, history, and receiving raw responses.
* **`discord_actions.py` (The Herald):**
    * Manages all Discord API interactions that are not the main message loop.
    * Handles sending replies, character limits, emoji reactions, and user tagging.
* **`memory_manager.py` (The Scribe):**
    * **The heart of memory management.** Houses all logic for managing conversation history, chunking, embedding, and database interaction.
    * Designed to be modular and platform-agnostic, allowing for local memory replacement of Discord history.
* **`utils.py` (The Artificer's Toolkit):**
    * Contains general utility functions (logging, keyword triggers, robust LLM response parsing, token counting).

---

### **3. Memory System Design (Phase 3: Building the Archives)**

This is the core of the project's intelligence.

* **3.1. Database Structure:** (Using SQLite for local persistence)
    * **`memory.db` file:** The single database file.
    * **`messages` Table:**
        * **Purpose:** Stores an immutable, versioned log of all messages the bot processes. This is the raw data source for chunks.
        * **Keying:** `unique_key` (PRIMARY KEY, e.g., `[bot_id]_[message_id]_[timestamp]`) to handle edited messages by creating new entries for each edit, thus preserving historical context.
        * **Columns:** `unique_key`, `message_id`, `author_id`, `timestamp` (ISO format), `content`, `bot_observer_id` (the bot that saw/processed the message), `edited_from_id` (optional, for tracing edits).
    * **`chunks` Table:**
        * **Purpose:** Stores processed, meaningful segments of conversation with their embeddings and associated metadata.
        * **Keying:** `chunk_id` (PRIMARY KEY, e.g., `[bot_id]_[model_response_timestamp]`) anchored to the bot's response that completes the segment.
        * **Columns:** `chunk_id`, `bot_id`, `model_response_timestamp`, `embedding_summary` (for oversized chunks), `embedding_vector` (BLOB), `message_keys` (JSON list of `unique_key`s from `messages` table), `summary_generated` (boolean), `reasoning_text` (the bot's internal thought/monologue), `created_at`.

* **3.2. Chunking Logic (`chunk_conversation` in `memory_manager.py`):**
    * **Strategy:** "Intelligently sectioned conversations" with "turns with an overlay for intelligent grouping".
    * **Delimitation:** Chunks primarily end at a model's response. Everything between two consecutive model responses forms a base segment.
    * **Oversized Chunk Handling:**
        * If a segment (especially human-to-human chat) exceeds `max_chunk_tokens`, it is summarized using a lightweight model (Gemini 1.5 Flash by default).
        * The chunk is then packaged as `[summary, ..., model response]`, backfilling recent direct messages up to the token limit (e.g., `[summary, user message[-2], user message[-1], model response]`).
        * The summary text is stored separately in `embedding_summary` and flagged with `summary_generated`.
    * **Token Counting:** Uses the same tokenizer as the embedding model (Qwen2Tokenizer for Stella models) for accurate length measurement. Tokenization is performed quickly on demand.
    * **Output:** Returns a list of structured chunk dictionaries.

* **3.3. Memory Processing Flow (`process_and_store_memory` in `memory_manager.py`):**
    * Called as an `asyncio.create_task` from `main.py` *after* the bot sends its response to Discord, ensuring it doesn't block user experience.
    * Constructs the current bot's message and appends it to the conversation `history`.
    * Invokes `chunk_conversation` with this combined history.
    * **(Future: Stores messages):** Will contain logic to insert all relevant messages (user, other bots, current bot's) from the processed history into the `messages` table.
    * **(Future: Stores chunks):** Will call functions to embed each `processed_chunk` and store it into the `chunks` table.

---

### **4. Key Components & Technologies**

* **`discord.py`:** For Discord API interaction.
* **SQLite3:** For local, file-based database persistence.
* **`python-dotenv`:** For environment variable management.
* **`transformers`:** For loading and using the tokenizer associated with embedding models.
* **`sentence-transformers`:** For loading and generating embeddings (e.g., `NovaSearch/stella_en_1.5B_v5`).
* **`faiss-cpu`:** For efficient local similarity search on embedding vectors.

---

### **5. Roadmap for Future Phases**

Once the core memory *writing* is fully implemented and stable:

* **Phase 4: Activating Memory (Retrieval & Usage)**
    * **Local Memory Reading:** Modify `get_chat_history` to retrieve context from the local database instead of Discord API calls.
    * **Thematic Resonance Search:** Implement the core logic for searching the FAISS index to retrieve semantically similar chunks.
    * **Integrating Retrieved Memory:** Pass relevant retrieved memories into the LLM's context for richer, more informed responses (e.g., as part of the system prompt or history).
* **Phase 5: Advanced AI Capabilities**
    * **Expanded Discord Functionality:** Implement support for Discord threads and attachments (reading and sending).
    * **Multi-Context/Platform Support:** Develop separate `main` entry points (e.g., `obsidian_main.py`, `web_ui_main.py`) that leverage the shared `llm_handler.py` and `memory_manager.py` to run the bots in different environments.
    * **Speech Output:** Implement text-to-speech capabilities for bots to "speak aloud."

---

### **6. Remaining Next Steps**
The following tasks will finish the foundation laid in Phase 1:

* **Complete Memory Persistence:** Finalize `process_and_store_memory` so messages and chunks are written to `memory.db` using helper functions.
* **Summarization for Oversized Segments:** Update `chunk_conversation` to detect when token limits are exceeded and call the LLM for concise summaries before storing.
    * The summarizer model defaults to **Gemini 1.5 Flash** and can be changed via `SUMMARIZER_MODEL_NAME` and `SUMMARIZER_MODEL_TYPE` in `config.py`.
* **Retrieval Phase Foundations:** Extend `get_chat_history` to pull context from the database and implement a FAISS search for similar chunks.

---

The kingdom awaits its next phase of construction!
