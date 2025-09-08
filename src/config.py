import dotenv
import os
import logging

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

PLAYLIST_ID = os.getenv("PLAYLIST_ID") or ""
DELETE_FROM_PLAYLIST = os.getenv("DELETE_FROM_PLAYLIST", "false").lower() == "true"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or ""
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH") or ""
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "3"))
