#!/usr/bin/env python3
"""
Simple test script for Ghost Brain.
"""

import asyncio
import os
from ghost_brain import Brain, BrainConfig


async def test_brain():
    """Test basic brain functionality."""
    print("🧠 Testing Ghost Brain...")
    
    # Create config with test settings
    config = BrainConfig(
        user_id="test_user",
        system_prompt="You are a helpful AI assistant for testing.",
        llm=BrainConfig.LLMConfig(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            gemini_api_key=os.getenv("GEMINI_API_KEY")
        )
    )
    
    # Initialize brain
    brain = Brain(config)
    await brain.initialize()
    
    # Test health check
    print("\n📊 Health Check:")
    health = await brain.health_check()
    print(f"Status: {health['status']}")
    print(f"Memory: {health['memory']}")
    print(f"LLM: {health['llm']}")
    
    if health['errors']:
        print(f"Errors: {health['errors']}")
    
    # Test memory stats
    print("\n📈 Memory Stats:")
    stats = await brain.get_memory_stats()
    print(f"User ID: {stats['user_id']}")
    print(f"DB Path: {stats['db_path']}")
    print(f"Embedding Model: {stats['embedding_model']}")
    
    # Test simple message processing
    print("\n💬 Testing Message Processing:")
    test_message = "Hello! This is a test message."
    
    try:
        result = await brain.process_message(
            message=test_message,
            use_structured_response=False  # Simpler for testing
        )
        
        print(f"Response: {result['response']}")
        print(f"Memory Chunks: {result['memory_chunks']}")
        print(f"Model Type: {result['model_type']}")
        
    except Exception as e:
        print(f"Error processing message: {e}")
    
    # Test memory search
    print("\n🔍 Testing Memory Search:")
    try:
        chunks = await brain.search_memory("test", top_k=2)
        print(f"Found {len(chunks)} memory chunks")
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i+1}: {chunk[:100]}...")
    except Exception as e:
        print(f"Error searching memory: {e}")
    
    print("\n✅ Brain test completed!")


if __name__ == "__main__":
    asyncio.run(test_brain()) 