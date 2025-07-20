# main.py
# The central orchestrator for the MMM-Bots project.

import discord
import asyncio
import datetime
import re
import os
import json

# Set DEBUG_MODE based on environment variable. Any debug print statements
# throughout this module will only execute when this is True.
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# --- DEBUGGING ENVIRONMENT VARIABLES ---
if DEBUG_MODE:
    print(
        f"DEBUG: Before dotenv load, DISCORD_TOKEN_CASSIUS: {os.environ.get('DISCORD_TOKEN_CASSIUS')}"
    )
from dotenv import load_dotenv  # Import load_dotenv here, as it's used by config.py
load_dotenv()  # Ensure .env is loaded
if DEBUG_MODE:
    print(
        f"DEBUG: After dotenv load, DISCORD_TOKEN_CASSIUS: {os.environ.get('DISCORD_TOKEN_CASSIUS')}"
    )
# --- END DEBUGGING ---

# Import our custom modules
from config import (
    BOT_CONFIG,
    SERVER_CONTEXT_FILE,
    MAX_TOKENS_FOR_RESPONSE,
    SUMMARIZER_MODEL_NAME,
    SUMMARIZER_MODEL_TYPE,
)
from llm_handler import get_llm_response
from discord_actions import send_bot_reply, process_special_commands
from memory_manager import get_chat_history, initialize_memory_database, process_and_store_memory # chunk_conversation removed for this version
from utils import log_message, check_keyword_trigger, parse_llm_response_robustly


# --- Globals ---
bot_personas = {}
shared_server_context = ""

async def run_bot(config_key, token):
    """
    Main function to initialize and run a single bot instance.
    """
    config = BOT_CONFIG[config_key]
    model_type = config['model_type']
    bot_triggers = config['triggers']

    # --- System Prompt Assembly ---
    try:
        with open(config['persona_file'], 'r', encoding='utf-8') as f:
            individual_persona = f.read()
        
        companion_details = ""
        if config.get('companion_file'):
            try:
                with open(config['companion_file'], 'r', encoding='utf-8') as f:
                    companion_details = f.read()
            except FileNotFoundError:
                log_message(config_key, f"Warning: Companion file '{config['companion_file']}' not found. Skipping.")

        # The full system prompt is assembled here
        bot_personas[config_key] = f"{individual_persona}\n\n{companion_details}\n\n{shared_server_context}"
        log_message(config_key, f"Successfully assembled system prompt for '{config_key}'.")

    except Exception as e:
        log_message(config_key, f"FATAL: Could not load persona for '{config_key}': {e}")
        return

    # --- Discord Client Setup ---
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        log_message(config_key, f"Logged in as {client.user}. Online and ready.")

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        # --- Advanced Trigger Logic ---
        triggered = False
        is_mention = client.user in message.mentions

        if message.author.bot:
            # Bots only trigger each other on explicit mentions, not replies.
            if is_mention:
                triggered = True
        else:
            # Humans can trigger on mention, reply, or keyword.
            is_reply_to_me = False
            if message.reference:
                try:
                    ref_msg = await message.channel.fetch_message(message.reference.message_id)
                    if ref_msg.author == client.user:
                        is_reply_to_me = True
                except (discord.NotFound, discord.HTTPException):
                    pass
            
            # Use the nuanced keyword check to respect the '!' escape character.
            triggered_by_keyword = check_keyword_trigger(message.content, bot_triggers)

            if is_mention or is_reply_to_me or triggered_by_keyword:
                triggered = True

        if not triggered:
            return

        # --- Main Response Logic ---
        log_message(config_key, f"Triggered by {message.author.name} in #{message.channel.name}")
        
        # Define logger here, at the top of on_message processing block
        logger = lambda msg: log_message(config_key, msg)

        # Debugging the variable assignments to pinpoint crash
        if DEBUG_MODE:
            print("DEBUG: Attempting to assign bot_user_id...")
        bot_user_id = str(client.user.id)
        if DEBUG_MODE:
            print(f"DEBUG: bot_user_id assigned: {bot_user_id}")

        if DEBUG_MODE:
            print("DEBUG: Attempting to assign max_chunk_tokens...")
        max_chunk_tokens = MAX_TOKENS_FOR_RESPONSE
        if DEBUG_MODE:
            print(f"DEBUG: max_chunk_tokens assigned: {max_chunk_tokens}")

        if DEBUG_MODE:
            print("DEBUG: Attempting to assign llm_summarizer_config...")
        llm_summarizer_config = {
            "model_type": SUMMARIZER_MODEL_TYPE,
            "model_name": SUMMARIZER_MODEL_NAME,
            "system_prompt": (
                "You are a helpful assistant tasked with summarizing conversation content. "
                "Provide a concise factual summary of the given text, focusing on key topics "
                "and information discussed. Do not add opinions or conversational filler."
            ),
        }
        if DEBUG_MODE:
            print("DEBUG: llm_summarizer_config assigned.")

        # This version assumes typing indicator is active
        async with message.channel.typing():
            logger(f"DEBUG: Typing indicator started. Entering message processing block...")

            logger(f"DEBUG: Starting get_chat_history...")
            history = await get_chat_history(message, logger=logger, bot_id=bot_user_id)
            logger(f"DEBUG: Finished get_chat_history. History length: {len(history)}")
            
            clean_content = re.sub(r'<@!?\d+>', '', message.content).strip()
            final_user_prompt = f"{message.author.display_name}: {clean_content}" if clean_content else "..."
            
            logger(f"DEBUG: Starting get_llm_response...")
            raw_response = await get_llm_response(
                model_type,
                bot_personas[config_key],
                history, # Still passing Discord history for LLM context for now
                final_user_prompt,
                logger=logger
            )
            logger(f"DEBUG: Finished get_llm_response. Raw response received.")

            # --- Structured JSON Response Processing ---
            parsed_data = parse_llm_response_robustly(raw_response, logger=logger)

            response_to_send_discord = "" # Initialize variable for the final content to send
            reasoning_to_store = "" # Initialize variable for reasoning

            if parsed_data:
                response_to_send_discord = parsed_data['response_to_user']
                reasoning_to_store = parsed_data['reasoning'] # Store reasoning for chunking
                logger(f"REASONING: {reasoning_to_store}") # Log reasoning

                # Process special commands for the response to send
                response_to_send_discord = await process_special_commands(response_to_send_discord, message, logger=logger)
            else:
                # Fallback if parsing fails (no valid JSON extracted/parsed)
                response_to_send_discord = raw_response # Use raw response as fallback
                reasoning_to_store = 'LLM response was not valid JSON.' # Default reasoning for fallback
                logger(f"!!! Failed to parse LLM response after robust attempts. Raw response: '{raw_response}'")
                # process_special_commands is not typically needed for raw fallback, but can be added if desired

            # --- Send response to Discord (always sends something) ---
            if response_to_send_discord: # Ensure there's content to send
                should_mention_author = not message.author.bot
                await send_bot_reply(message, response_to_send_discord, mention_author=should_mention_author, logger=logger)
                logger(f"DEBUG: Response sent to Discord.")
                
                # --- Call process_and_store_memory as background task AFTER response is sent ---
                # This ensures memory processing happens regardless of JSON parsing success
                logger(f"DEBUG: Calling process_and_store_memory as background task...")
                asyncio.create_task(
                    process_and_store_memory(
                        bot_user_id=bot_user_id,
                        max_chunk_tokens=max_chunk_tokens,
                        logger=logger,
                        llm_summarizer_config=llm_summarizer_config,
                        history=history, # Pass the original history from main.py
                        response_to_send_discord=response_to_send_discord, # The actual content sent to discord
                        reasoning_to_store=reasoning_to_store, # The reasoning generated by the LLM
                        message_id=str(message.id) # Original Discord message ID that triggered response
                    )
                )
                logger(f"DEBUG: Memory processing task initiated.")
            else:
                logger(f"WARNING: No content to send to Discord after processing. Raw response: '{raw_response}'")

    # This part belongs to run_bot, outside of on_message
    try:
        await client.start(token)
    except Exception as e:
        log_message(config_key, f"FATAL: Discord client failed to start for {config_key}: {e}")
        log_message(config_key, f"Provided token was: {token}")


async def main():
    """
    Main entry point that loads shared context and starts all configured bots.
    """
    global shared_server_context
    try:
        with open(SERVER_CONTEXT_FILE, 'r', encoding='utf-8') as f:
            shared_server_context = f.read()
        log_message("System", f"Successfully loaded shared context from '{SERVER_CONTEXT_FILE}'.")
    except Exception as e:
        log_message("System", f"Warning: Could not load server context: {e}.")

    db_path = "memory.db"
    logger_func = lambda msg: log_message("System", msg)
    initialize_memory_database(db_path, logger_func)

    tasks = []
    log_message("System", "Preparing to configure bots...")
    for key, config in BOT_CONFIG.items():
        token_name = config['token_env']
        token = os.getenv(token_name)

        log_message("System", f"  -> Checking for bot: {key}. Needs token: {token_name}. Found: {'Yes' if token else 'No'}")

        if not token:
            log_message("System", f"FATAL: Discord token '{token_name}' not found for {key}. Skipping.")
            continue
        tasks.append(run_bot(key, token))

    if tasks:
        log_message("System", f"Configuration complete. Attempting to start {len(tasks)} bot(s)...")
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            log_message("System", f"FATAL: An unhandled error occurred during bot startup: {e}")
    else:
        log_message("System", "Configuration failed. No bots were able to start. Please check your .env file.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBots shutting down.")
