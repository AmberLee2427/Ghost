"""
HTTP server for Ghost Brain.
"""

import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from .brain import Brain
from .config import BrainConfig


# API Models
class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = None
    user_id: Optional[str] = None
    system_prompt: Optional[str] = None
    model_type: Optional[str] = None
    model_name: Optional[str] = None
    use_structured_response: bool = True


class ChatResponse(BaseModel):
    response: str
    reasoning: Optional[str] = None
    memory_chunks: int
    timestamp: str
    model_type: str
    model_name: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3


class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    initialized: bool
    memory: str
    llm: str
    errors: List[str]


# Global brain instance
brain: Optional[Brain] = None


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Ghost Brain API",
        description="Intelligent AI brain with memory management and RAG capabilities",
        version="0.0.1"
    )
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize brain on startup."""
        global brain
        brain = Brain()
        await brain.initialize()
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        if not brain:
            raise HTTPException(status_code=503, detail="Brain not initialized")
        
        return await brain.health_check()
    
    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        """Process a chat message."""
        if not brain:
            raise HTTPException(status_code=503, detail="Brain not initialized")
        
        try:
            result = await brain.process_message(
                message=request.message,
                history=request.history,
                user_id=request.user_id,
                system_prompt=request.system_prompt,
                model_type=request.model_type,
                model_name=request.model_name,
                use_structured_response=request.use_structured_response
            )
            return ChatResponse(**result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    
    @app.post("/memory/search")
    async def search_memory(request: SearchRequest):
        """Search memory for relevant chunks."""
        if not brain:
            raise HTTPException(status_code=503, detail="Brain not initialized")
        
        try:
            chunks = await brain.search_memory(request.query, request.top_k)
            return {"chunks": chunks, "query": request.query, "top_k": request.top_k}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
    
    @app.get("/memory/stats")
    async def get_memory_stats():
        """Get memory statistics."""
        if not brain:
            raise HTTPException(status_code=503, detail="Brain not initialized")
        
        try:
            return await brain.get_memory_stats()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")
    
    @app.post("/config/update")
    async def update_config(request: ConfigUpdateRequest):
        """Update brain configuration."""
        if not brain:
            raise HTTPException(status_code=503, detail="Brain not initialized")
        
        try:
            await brain.update_config(request.config)
            return {"status": "updated", "config": request.config}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Config update error: {str(e)}")
    
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Ghost Brain API",
            "version": "0.0.1",
            "endpoints": [
                "GET /health - Health check",
                "POST /chat - Process chat message",
                "POST /memory/search - Search memory",
                "GET /memory/stats - Get memory statistics",
                "POST /config/update - Update configuration"
            ]
        }
    
    return app


def main():
    """Main entry point for the brain server."""
    app = create_app()
    
    print("Starting Ghost Brain server...")
    print("API will be available at: http://localhost:8000")
    print("Health check: http://localhost:8000/health")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main() 