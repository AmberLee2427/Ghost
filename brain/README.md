# Ghost Brain

The intelligent AI brain component for the Ghost project, providing memory management, RAG capabilities, and LLM integration.

## Features

- **Memory Management**: SQLite-based conversation history with embeddings
- **RAG System**: Semantic search with citations using `txtai`
- **LLM Integration**: Support for OpenAI and Google Gemini models
- **HTTP API**: RESTful interface for plugin communication
- **Intelligent Chunking**: Automatic conversation segmentation and summarization

## Installation

```bash
pip install -e .
```

## Usage

### As a Service
```bash
ghost-brain
```

### As a Python Package
```python
from ghost_brain import Brain

brain = Brain()
response = await brain.process_message("Hello, how are you?")
```

## Development

```bash
# Create the dev environment
python -m venv ghost-brain-env
ghost-brain-env\Scripts\activate.bat
pip install -r requirements.txt

# Install in editable mode
pip install -e .

# Run tests
pytest

# Start development server
uvicorn ghost_brain.server:app --reload
```

## API Endpoints

- `POST /chat` - Process a chat message
- `GET /health` - Health check
- `POST /memory/search` - Search memory
- `GET /settings` - Get current settings
- `POST /settings` - Update settings

## Architecture

The brain consists of several core modules:

- **Memory Manager**: Handles conversation storage and retrieval
- **LLM Handler**: Manages API calls to language models
- **RAG Engine**: Provides semantic search capabilities
- **HTTP Server**: Exposes functionality via REST API 