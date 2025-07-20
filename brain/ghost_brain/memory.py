"""
Memory management for Ghost Brain.
"""

import datetime
import asyncio
import json
import sqlite3
from collections import deque
import numpy as np
import faiss
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional

from .config import BrainConfig


class MemoryManager:
    """Manages conversation memory with embeddings and RAG capabilities."""
    
    def __init__(self, config: BrainConfig):
        self.config = config
        self._embedding_tokenizer = None
        self._embedding_model = None
        self._embedding_model_name = config.memory.embedding_model
        
    def _load_embedding_model_once(self):
        """Load embedding model globally once for efficiency."""
        if self._embedding_model is None:
            try:
                self._embedding_model = SentenceTransformer(self._embedding_model_name)
                print(f"Loaded embedding model: {self._embedding_model_name}")
            except Exception as e:
                print(f"Error loading embedding model: {e}")
                self._embedding_model = None
        return self._embedding_model

    def _load_tokenizer_once(self):
        """Load tokenizer globally once for efficiency."""
        if self._embedding_tokenizer is None:
            try:
                self._embedding_tokenizer = AutoTokenizer.from_pretrained(self._embedding_model_name)
                print(f"Loaded tokenizer: {self._embedding_model_name}")
            except Exception as e:
                print(f"Error loading tokenizer: {e}")
                self._embedding_tokenizer = None
        return self._embedding_tokenizer

    def get_token_count(self, text: str) -> int:
        """Get token count for text using the embedding model's tokenizer."""
        tokenizer = self._load_tokenizer_once()
        if tokenizer:
            return len(tokenizer.encode(text))
        else:
            print("WARNING: Tokenizer not loaded. Falling back to word count.")
            return len(text.split())

    def initialize_database(self):
        """Initialize the memory database with required tables."""
        conn = sqlite3.connect(self.config.memory.db_path)
        cursor = conn.cursor()

        # Messages table - stores raw conversation data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                unique_key TEXT PRIMARY KEY,
                message_id TEXT,
                author_id TEXT,
                timestamp TEXT,
                content TEXT,
                user_id TEXT,
                edited_from_id TEXT
            )
        """)

        # Chunks table - stores processed conversation segments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                user_id TEXT,
                model_response_timestamp TEXT,
                embedding_summary TEXT,
                embedding_vector BLOB,
                message_keys TEXT,
                summary_generated BOOLEAN,
                reasoning_text TEXT,
                created_at TEXT
            )
        """)

        conn.commit()
        conn.close()
        print(f"Initialized memory database: {self.config.memory.db_path}")

    async def search_similar_chunks(self, query_text: str, top_k: int = 3) -> List[str]:
        """Search for similar conversation chunks using FAISS."""
        embedding_model = self._load_embedding_model_once()
        if embedding_model is None:
            print("FATAL: Embedding model not loaded. Cannot perform similarity search.")
            return []

        def _fetch_chunks():
            conn = sqlite3.connect(self.config.memory.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT chunk_id, embedding_summary, embedding_vector, message_keys, summary_generated FROM chunks WHERE user_id=?",
                (self.config.user_id,)
            )
            rows = cursor.fetchall()
            conn.close()
            return rows

        rows = await asyncio.to_thread(_fetch_chunks)
        if not rows:
            return []

        vectors = [np.frombuffer(r[2], dtype="float32") for r in rows]
        dimension = vectors[0].shape[0]
        index = faiss.IndexFlatL2(dimension)
        index.add(np.vstack(vectors))

        query_vec = embedding_model.encode([query_text]).astype("float32")
        _d, retrieved_idx = index.search(query_vec, min(top_k, len(vectors)))

        similar_chunks = []

        for idx in retrieved_idx[0]:
            chunk_id, embedding_summary, _vec, message_keys_json, summary_generated = rows[idx]
            message_keys = json.loads(message_keys_json)

            def _fetch_messages(keys):
                if not keys:
                    return []
                conn = sqlite3.connect(self.config.memory.db_path)
                cursor = conn.cursor()
                placeholders = ",".join(["?" for _ in keys])
                cursor.execute(
                    f"SELECT unique_key, content FROM messages WHERE unique_key IN ({placeholders})",
                    keys
                )
                data = cursor.fetchall()
                conn.close()
                mapping = {k: v for k, v in data}
                return [mapping.get(k, "") for k in keys]

            messages = await asyncio.to_thread(_fetch_messages, message_keys)

            chunk_parts = []
            if summary_generated and embedding_summary:
                chunk_parts.append(embedding_summary)
            chunk_parts.extend(messages)

            similar_chunks.append("\n".join(chunk_parts))

        return similar_chunks

    async def get_chat_history(self, current_message: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent chat history combined with relevant memory."""
        # For now, return empty history - this will be populated by the calling application
        history_messages = []

        # Retrieve additional context from memory database
        try:
            retrieved = await self.search_similar_chunks(
                current_message,
                top_k=self.config.memory.retrieval_k
            )
            for chunk in retrieved[::-1]:
                history_messages.insert(
                    0,
                    {
                        "role": "system",
                        "content": chunk,
                        "author_id": "memory",
                        "timestamp": "0",
                        "message_id": "0",
                    }
                )
        except Exception as e:
            print(f"Error retrieving similar chunks: {e}")

        return history_messages

    async def store_messages(self, messages: List[Dict[str, Any]]):
        """Store messages in the database."""
        def _store():
            conn = sqlite3.connect(self.config.memory.db_path)
            cursor = conn.cursor()
            
            for msg in messages:
                unique_key = f"{self.config.user_id}_{msg['message_id']}_{msg['timestamp']}"
                cursor.execute(
                    "INSERT OR REPLACE INTO messages (unique_key, message_id, author_id, timestamp, content, user_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (unique_key, msg['message_id'], msg['author_id'], msg['timestamp'], msg['content'], self.config.user_id)
                )
            
            conn.commit()
            conn.close()

        await asyncio.to_thread(_store)

    async def store_chunks(self, chunks: List[Dict[str, Any]], reasoning_text: str):
        """Store conversation chunks in the database."""
        embedding_model = self._load_embedding_model_once()
        if embedding_model is None:
            print("ERROR: Cannot store chunks without embedding model")
            return

        def _store():
            conn = sqlite3.connect(self.config.memory.db_path)
            cursor = conn.cursor()
            
            for chunk in chunks:
                chunk_id = f"{self.config.user_id}_{chunk['timestamp']}"
                
                # Create embedding for the chunk content
                chunk_content = "\n".join(chunk['messages'])
                embedding = embedding_model.encode([chunk_content]).astype("float32")
                
                cursor.execute(
                    """INSERT OR REPLACE INTO chunks 
                       (chunk_id, user_id, model_response_timestamp, embedding_summary, embedding_vector, message_keys, summary_generated, reasoning_text, created_at) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        chunk_id,
                        self.config.user_id,
                        chunk['timestamp'],
                        chunk.get('summary', ''),
                        embedding.tobytes(),
                        json.dumps(chunk['message_keys']),
                        chunk.get('summary_generated', False),
                        reasoning_text,
                        datetime.datetime.now().isoformat()
                    )
                )
            
            conn.commit()
            conn.close()

        await asyncio.to_thread(_store)

    async def chunk_conversation(self, conversation_history: List[Dict[str, Any]], max_chunk_tokens: int) -> List[Dict[str, Any]]:
        """Intelligently chunk conversation history."""
        chunks = []
        current_chunk = {
            'messages': [],
            'message_keys': [],
            'timestamp': datetime.datetime.now().isoformat(),
            'token_count': 0
        }

        for msg in conversation_history:
            msg_content = msg['content']
            msg_tokens = self.get_token_count(msg_content)
            
            # If adding this message would exceed the limit, finalize current chunk
            if current_chunk['token_count'] + msg_tokens > max_chunk_tokens and current_chunk['messages']:
                chunks.append(current_chunk)
                current_chunk = {
                    'messages': [],
                    'message_keys': [],
                    'timestamp': datetime.datetime.now().isoformat(),
                    'token_count': 0
                }
            
            # Add message to current chunk
            current_chunk['messages'].append(msg_content)
            current_chunk['message_keys'].append(f"{self.config.user_id}_{msg['message_id']}_{msg['timestamp']}")
            current_chunk['token_count'] += msg_tokens

        # Add final chunk if it has content
        if current_chunk['messages']:
            chunks.append(current_chunk)

        return chunks

    async def process_and_store_memory(self, history: List[Dict[str, Any]], response: str, reasoning: str):
        """Process conversation and store in memory."""
        # Store messages
        await self.store_messages(history)
        
        # Create chunks
        chunks = await self.chunk_conversation(history, self.config.memory.max_chunk_tokens)
        
        # Store chunks
        await self.store_chunks(chunks, reasoning)
        
        print(f"Stored {len(history)} messages and {len(chunks)} chunks in memory") 