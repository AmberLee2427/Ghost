# config.py
import os
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OWNER_USER_ID = os.getenv("OWNER_USER_ID")

# --- API and Model Settings ---
OPENAI_MODEL_NAME = "gpt-4o"
GEMINI_MODEL_NAME = "gemini-1.5-pro-latest"
SUMMARIZER_MODEL_NAME = "gemini-1.5-flash-latest"
SUMMARIZER_MODEL_TYPE = "gemini"
MAX_TOKENS_FOR_RESPONSE = 1500
BASE_TEMPERATURE = 0.8

# --- File Paths ---
SERVER_CONTEXT_FILE = "server-context.txt"

# --- Bot Configuration ---
BOT_CONFIG = {
    "CASSIUS": {
        "model_type": "openai",
        "token_env": "DISCORD_TOKEN_CASSIUS",
        "persona_file": "cassius.txt",
        "companion_file": "amber.txt",
        "triggers": ["cassius", "cas", "cass"]
    },
    "YUANJI": {
        "model_type": "gemini",
        "token_env": "DISCORD_TOKEN_YUANJI",
        "persona_file": "yuanji.txt",
        "companion_file": "dylan.txt",
        "triggers": ["yuanji", "yuan"]
    }
}