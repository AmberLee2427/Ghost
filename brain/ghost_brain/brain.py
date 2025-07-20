"""
Main Brain class for Ghost AI.
"""

import datetime
import asyncio
from typing import List, Dict, Any, Optional, Tuple

from .config import BrainConfig
from .memory import MemoryManager
from .llm import LLMHandler


class Brain:
    """Main brain class that orchestrates memory and LLM functionality."""
    
    def __init__(self, config: Optional[BrainConfig] = None):
        self.config = config or BrainConfig()
        self.memory = MemoryManager(self.config)
        self.llm = LLMHandler(self.config)
        self._initialized = False
        
    async def initialize(self):
        """Initialize the brain components."""
        if self._initialized:
            return
            
        print("Initializing Ghost Brain...")
        
        # Initialize memory database
        self.memory.initialize_database()
        
        # Test LLM connectivity
        await self._test_llm_connectivity()
        
        self._initialized = True
        print("Ghost Brain initialized successfully!")
        
    async def _test_llm_connectivity(self):
        """Test LLM connectivity."""
        print("Testing LLM connectivity...")
        
        if self.config.llm.openai_api_key:
            print("✓ OpenAI API key configured")
        if self.config.llm.gemini_api_key:
            print("✓ Gemini API key configured")
            
        if not self.config.llm.openai_api_key and not self.config.llm.gemini_api_key:
            print("⚠ No LLM API keys configured")
            
    async def process_message(
        self, 
        message: str, 
        history: Optional[List[Dict[str, Any]]] = None,
        user_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model_type: Optional[str] = None,
        model_name: Optional[str] = None,
        use_structured_response: bool = True
    ) -> Dict[str, Any]:
        """Process a message and return response with memory integration."""
        
        if not self._initialized:
            await self.initialize()
            
        # Update user_id if provided
        if user_id:
            self.config.user_id = user_id
            
        # Use provided system prompt or default
        system_prompt = system_prompt or self.config.system_prompt
        
        # Get chat history with memory integration
        memory_history = await self.memory.get_chat_history(message)
        
        # Combine provided history with memory
        full_history = []
        if history:
            full_history.extend(history)
        full_history.extend(memory_history)
        
        # Create user prompt
        user_prompt = f"User: {message}"
        
        # Get LLM response
        if use_structured_response:
            structured_prompt = self.llm.create_structured_prompt(system_prompt)
            raw_response = await self.llm.get_response(
                system_prompt=structured_prompt,
                history=full_history,
                user_prompt=user_prompt,
                model_type=model_type,
                model_name=model_name
            )
            
            # Parse structured response
            response_to_user, reasoning = self.llm.parse_structured_response(raw_response or "")
        else:
            raw_response = await self.llm.get_response(
                system_prompt=system_prompt,
                history=full_history,
                user_prompt=user_prompt,
                model_type=model_type,
                model_name=model_name
            )
            response_to_user = raw_response or ""
            reasoning = None
            
        # Store in memory (background task)
        if history:
            asyncio.create_task(
                self.memory.process_and_store_memory(
                    history=history + [{"role": "user", "content": message, "message_id": "temp", "timestamp": datetime.datetime.now().isoformat(), "author_id": user_id or "user"}],
                    response=response_to_user,
                    reasoning=reasoning or "No reasoning provided"
                )
            )
            
        return {
            "response": response_to_user,
            "reasoning": reasoning,
            "memory_chunks": len(memory_history),
            "timestamp": datetime.datetime.now().isoformat(),
            "model_type": model_type or "auto",
            "model_name": model_name or "auto"
        }
        
    async def search_memory(self, query: str, top_k: int = 3) -> List[str]:
        """Search memory for relevant chunks."""
        if not self._initialized:
            await self.initialize()
            
        return await self.memory.search_similar_chunks(query, top_k)
        
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        if not self._initialized:
            await self.initialize()
            
        # This would require additional database queries
        # For now, return basic info
        return {
            "user_id": self.config.user_id,
            "db_path": self.config.memory.db_path,
            "embedding_model": self.config.memory.embedding_model,
            "initialized": self._initialized
        }
        
    async def update_config(self, new_config: Dict[str, Any]):
        """Update brain configuration."""
        # Update config fields
        for key, value in new_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            elif hasattr(self.config.llm, key):
                setattr(self.config.llm, key, value)
            elif hasattr(self.config.memory, key):
                setattr(self.config.memory, key, value)
                
        # Reinitialize if needed
        if self._initialized:
            await self.initialize()
            
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on brain components."""
        health = {
            "status": "healthy",
            "initialized": self._initialized,
            "memory": "ok",
            "llm": "ok",
            "errors": []
        }
        
        try:
            # Test memory
            if not self._initialized:
                await self.initialize()
        except Exception as e:
            health["memory"] = "error"
            health["errors"].append(f"Memory error: {e}")
            health["status"] = "unhealthy"
            
        try:
            # Test LLM (basic connectivity)
            if not self.config.llm.openai_api_key and not self.config.llm.gemini_api_key:
                health["llm"] = "no_keys"
                health["errors"].append("No LLM API keys configured")
        except Exception as e:
            health["llm"] = "error"
            health["errors"].append(f"LLM error: {e}")
            health["status"] = "unhealthy"
            
        return health 