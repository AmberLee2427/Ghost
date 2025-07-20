"""
Configuration management for Ghost Brain.
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel


class LLMConfig(BaseModel):
    """Configuration for LLM providers."""
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    gemini_model: str = "gemini-1.5-pro-latest"
    summarizer_model: str = "gemini-1.5-flash-latest"
    summarizer_type: str = "gemini"
    max_tokens: int = 1500
    temperature: float = 0.8


class MemoryConfig(BaseModel):
    """Configuration for memory management."""
    db_path: str = "memory.db"
    embedding_model: str = "NovaSearch/stella_en_1.5B_v5"
    max_chunk_tokens: int = 1500
    retrieval_k: int = 3


class BrainConfig(BaseModel):
    """Main configuration for Ghost Brain."""
    llm: LLMConfig = LLMConfig()
    memory: MemoryConfig = MemoryConfig()
    system_prompt: str = "You are a helpful AI assistant."
    user_id: str = "default_user"
    
    def __init__(self, **data):
        super().__init__(**data)
        # Load environment variables if not provided
        if not self.llm.openai_api_key:
            self.llm.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.llm.gemini_api_key:
            self.llm.gemini_api_key = os.getenv("GEMINI_API_KEY")


# Default configuration
DEFAULT_CONFIG = BrainConfig() 