# memory_manager.py
import datetime
import asyncio
import json
import sqlite3
from collections import deque
import numpy as np
import faiss
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer

# Import components for LLM calls for summarization
from llm_handler import get_llm_response
from config import BOT_CONFIG, MAX_TOKENS_FOR_RESPONSE # Ensure MAX_TOKENS_FOR_RESPONSE is imported from config


# --- Global tokenizer instance ---
_embedding_tokenizer = None
_embedding_model_name_for_tokenizer = "NovaSearch/stella_en_1.5B_v5" # Corrected model name

# --- Global embedding model instance ---
_embedding_model = None

def _load_embedding_model_once(model_name: str):
    global _embedding_model
    if _embedding_model is None:
        logger_func = lambda msg: print(f"DEBUG: {msg}")
        logger_func(f"Attempting to load embedding model for: {model_name}...")
        try:
            _embedding_model = SentenceTransformer(model_name)
            logger_func(f"Loaded embedding model for {model_name} successfully.")
        except Exception as e:
            logger_func(f"Error loading embedding model for {model_name}: {e}")
            _embedding_model = None
    return _embedding_model

def _load_tokenizer_once(model_name: str):
    global _embedding_tokenizer
    if _embedding_tokenizer is None:
        logger_func = lambda msg: print(f"DEBUG: {msg}")
        logger_func(f"Attempting to load tokenizer for: {model_name}...")
        try:
            _embedding_tokenizer = AutoTokenizer.from_pretrained(model_name)
            logger_func(f"Loaded tokenizer for {model_name} successfully.")
        except Exception as e:
            logger_func(f"Error loading tokenizer for {model_name}: {e}")
            _embedding_tokenizer = None
    return _embedding_tokenizer

def get_token_count(text: str, logger=None) -> int:
    """
    Measures the token length of a given text using the embedding model's tokenizer.
    Loads the tokenizer globally once for efficiency.
    """
    tokenizer = _load_tokenizer_once(_embedding_model_name_for_tokenizer)
    if tokenizer:
        token_count = len(tokenizer.encode(text))
        if logger:
            logger(f"DEBUG: Text token count: {token_count} for '{text[:50]}...'")
        return token_count
    else:
        if logger:
            logger("WARNING: Tokenizer not loaded. Falling back to word count for token estimation.")
        return len(text.split())


async def search_similar_chunks(query_text: str, bot_id: str, top_k: int = 3, logger=None, db_path: str = "memory.db") -> list:
    """Retrieve up to top_k similar chunks from the database using FAISS."""

    embedding_model = _load_embedding_model_once(_embedding_model_name_for_tokenizer)
    if embedding_model is None:
        if logger:
            logger("FATAL: Embedding model not loaded. Cannot perform similarity search.")
        return []

    def _fetch_chunks():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT chunk_id, embedding_summary, embedding_vector, message_keys, summary_generated FROM chunks WHERE bot_id=?",
            (bot_id,),
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
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            placeholders = ",".join(["?" for _ in keys])
            cursor.execute(
                f"SELECT unique_key, content FROM messages WHERE unique_key IN ({placeholders})",
                keys,
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


async def get_chat_history(message, limit=10, logger=None, bot_id=None, db_path: str = "memory.db", retrieval_k: int = 3):
    """Return recent Discord history combined with relevant past memory."""
    history_messages = []
    try:
        async for hist_msg in message.channel.history(limit=limit + 1, oldest_first=False):
            if hist_msg.id == message.id:
                continue

            content = hist_msg.content
            role = "user"

            if hist_msg.author.id == message.guild.me.id:
                role = "model"
            else:
                content = f"{hist_msg.author.display_name}: {content}"

            history_messages.append({
                "role": role,
                "content": content,
                "author_id": str(hist_msg.author.id),
                "timestamp": hist_msg.created_at.isoformat(),
                "message_id": str(hist_msg.id)
            })
            if len(history_messages) >= limit:
                break
    except Exception as e:
        if logger:
            logger(f"Error fetching history: {e}")

    history_messages = history_messages[::-1]

    # Retrieve additional context from memory database if bot_id provided
    if bot_id:
        try:
            query_text = message.content
            retrieved = await search_similar_chunks(
                query_text,
                bot_id=bot_id,
                top_k=retrieval_k,
                logger=logger,
                db_path=db_path,
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
                    },
                )
        except Exception as e:
            if logger:
                logger(f"Error retrieving similar chunks: {e}")

    return history_messages


def initialize_memory_database(db_path: str, logger):
    # ... (this function remains unchanged) ...
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS messages (
                unique_key TEXT PRIMARY KEY,
                message_id TEXT NOT NULL,
                author_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                content TEXT NOT NULL,
                bot_observer_id TEXT NOT NULL,
                edited_from_id TEXT
            )
        """)

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                bot_id TEXT NOT NULL,
                model_response_timestamp TEXT NOT NULL,
                embedding_summary TEXT,
                embedding_vector BLOB,
                message_keys TEXT NOT NULL,
                summary_generated INTEGER NOT NULL,
                reasoning_text TEXT,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        logger(f"Memory database '{db_path}' initialized successfully.")

    except sqlite3.Error as e:
        logger(f"FATAL: SQLite database initialization failed: {e}")
    finally:
        if conn:
            conn.close()


async def store_messages_to_db(messages: list, bot_id: str, logger, db_path: str = "memory.db"):
    """Persist a list of message dictionaries into the messages table."""

    def _store():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for msg in messages:
            unique_key = f"{bot_id}_{msg['message_id']}_{msg['timestamp']}"
            cursor.execute(
                """
                INSERT OR IGNORE INTO messages (
                    unique_key, message_id, author_id, timestamp, content, bot_observer_id, edited_from_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    unique_key,
                    msg["message_id"],
                    msg["author_id"],
                    msg["timestamp"],
                    msg["content"],
                    bot_id,
                    msg.get("edited_from_id"),
                ),
            )
        conn.commit()
        conn.close()

    await asyncio.to_thread(_store)
    logger(f"DEBUG: Stored {len(messages)} messages to DB.")


async def store_chunks_to_db(chunks: list, bot_id: str, logger, reasoning_text: str, db_path: str = "memory.db"):
    """Generate embeddings and store chunks into the database."""

    embedding_model = _load_embedding_model_once(_embedding_model_name_for_tokenizer)
    if embedding_model is None:
        logger("FATAL: Embedding model not loaded. Skipping chunk storage.")
        return

    def _store():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for chunk in chunks:
            chunk_id = f"{bot_id}_{chunk['timestamp']}"
            vector = embedding_model.encode(chunk["content"]).astype("float32")
            cursor.execute(
                """
                INSERT OR REPLACE INTO chunks (
                    chunk_id, bot_id, model_response_timestamp,
                    embedding_summary, embedding_vector, message_keys,
                    summary_generated, reasoning_text, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk_id,
                    bot_id,
                    chunk["timestamp"],
                    chunk.get("embedding_summary"),
                    vector.tobytes(),
                    json.dumps(chunk["original_message_keys"]),
                    int(chunk.get("summary_generated", False)),
                    reasoning_text,
                    datetime.datetime.now().isoformat(),
                ),
            )
        conn.commit()
        conn.close()

    await asyncio.to_thread(_store)
    logger(f"DEBUG: Stored {len(chunks)} chunks to DB.")


async def chunk_conversation(
    conversation_history: list,
    bot_user_id: str,
    max_chunk_tokens: int,
    logger,
    llm_summarizer_config: dict
) -> list:
    # ... (this function remains unchanged) ...
    chunks = []
    current_segment_messages = []

    for i, message in enumerate(conversation_history):
        current_segment_messages.append(message)

        if message["role"] == "model" and message["author_id"] == bot_user_id:
            bot_response = current_segment_messages[-1]
            pre_context_messages = current_segment_messages[:-1]

            chunk_content_parts = []
            original_message_ids = []
            summary_generated = False

            segment_text_for_len_check = "\n".join([msg['content'] for msg in pre_context_messages]) + "\n" + bot_response['content']
            
            current_segment_token_count = get_token_count(segment_text_for_len_check, logger)

            if current_segment_token_count > max_chunk_tokens:
                logger(
                    f"WARNING: Chunk for bot '{bot_user_id}' (ending with message ID {bot_response['message_id']}) is too long ({current_segment_token_count} tokens). Summarizing."
                )

                summary_text = await get_llm_response(
                    llm_summarizer_config["model_type"],
                    llm_summarizer_config["system_prompt"],
                    [],
                    "\n".join(msg["content"] for msg in pre_context_messages),
                    logger,
                    model_name=llm_summarizer_config.get("model_name"),
                )

                if not summary_text:
                    logger(
                        "ERROR: Summarization failed. Skipping this chunk altogether."
                    )
                    current_segment_messages = []
                    continue

                summary_generated = True
                embedding_summary = summary_text

                # Determine which recent messages can fit alongside the summary
                remaining_tokens = max_chunk_tokens - get_token_count(
                    summary_text, logger
                ) - get_token_count(bot_response["content"], logger)

                messages_to_include = []
                for msg in reversed(pre_context_messages):
                    msg_tokens = get_token_count(msg["content"], logger)
                    if remaining_tokens - msg_tokens >= 0:
                        messages_to_include.insert(0, msg)
                        remaining_tokens -= msg_tokens
                    else:
                        break

                chunk_content_parts.append(summary_text)
                for msg in messages_to_include:
                    chunk_content_parts.append(msg["content"])
                for msg in pre_context_messages:
                    original_message_ids.append(
                        f"{bot_user_id}_{msg['message_id']}_{msg['timestamp']}"
                    )
            else:
                for msg in pre_context_messages:
                    chunk_content_parts.append(msg["content"])
                    original_message_ids.append(
                        f"{bot_user_id}_{msg['message_id']}_{msg['timestamp']}"
                    )

                embedding_summary = None

            chunk_content_parts.append(bot_response["content"])
            original_message_ids.append(
                f"{bot_user_id}_{bot_response['message_id']}_{bot_response['timestamp']}"
            )

            final_chunk_content = "\n".join(chunk_content_parts)

            chunks.append(
                {
                    "content": final_chunk_content,
                    "timestamp": bot_response["timestamp"],
                    "bot_id": bot_user_id,
                    "original_message_keys": original_message_ids,
                    "summary_generated": summary_generated,
                    "embedding_summary": embedding_summary,
                }
            )

            current_segment_messages = []

    if current_segment_messages:
        logger(f"Chunking: Remaining messages at end of history (not yet chunked): {len(current_segment_messages)} messages. Will be processed with next bot response.")

    return chunks


# --- NEW FUNCTION: process_and_store_memory ---
async def process_and_store_memory(
    bot_user_id: str,
    max_chunk_tokens: int,
    logger,
    llm_summarizer_config: dict,
    history: list, # Pass the original history from main.py
    response_to_send_discord: str, # The actual content sent to discord
    reasoning_to_store: str, # The reasoning generated by the LLM
    message_id: str, # Original Discord message ID that triggered response
    db_path: str = "memory.db"
):
    """
    Encapsulates the full memory processing pipeline for a single bot interaction:
    1. Constructs the current bot's message for chunking.
    2. Appends it to the conversation history.
    3. Calls chunk_conversation to segment the history.
    4. Stores messages and chunks into the database.
    """
    logger(f"DEBUG: Entering process_and_store_memory for bot {bot_user_id}...")

    try:
        # 1. Construct the current bot's message for chunking
        current_bot_message_for_chunking = {
            "role": "model",
            "content": response_to_send_discord,
            "author_id": bot_user_id,
            "timestamp": datetime.datetime.now().isoformat(), # Use current time for response
            "message_id": message_id + "_bot_response" # A unique ID for this bot response
        }
        logger(f"DEBUG: current_bot_message_for_chunking constructed.")

        # 2. Append it to the conversation history for chunking
        full_history_for_chunking = history + [current_bot_message_for_chunking]
        logger(f"DEBUG: full_history_for_chunking constructed.")

        # 3. Call chunk_conversation to segment the history
        processed_chunks = await chunk_conversation(
            full_history_for_chunking,
            bot_user_id,
            max_chunk_tokens,
            logger,
            llm_summarizer_config
        )
        logger(f"DEBUG: Finished chunk_conversation. Chunks processed: {len(processed_chunks)} for bot {bot_user_id}.")

        # 4. Store messages in the database
        await store_messages_to_db(full_history_for_chunking, bot_user_id, logger, db_path)

        # 5. Store chunks in the database
        await store_chunks_to_db(processed_chunks, bot_user_id, logger, reasoning_to_store, db_path)

    except Exception as e:
        logger(f"FATAL: Error in process_and_store_memory for bot {bot_user_id}: {e}")
