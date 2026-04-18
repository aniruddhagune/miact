import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MIACT Project Variables
# Central configuration file for environment-specific settings.

# ── Database ─────────────────────────────────────────────────
DB_NAME = os.getenv("DB_NAME", "miact")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# ── Debug Mode ────────────────────────────────────────────────
# When True, all pipeline stages print verbose diagnostic output.
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

# Service-specific debugging (e.g., "SEARCH,NLP,DATABASE")
# If empty or "*", all services are logged.
DEBUG_SERVICES = os.getenv("MIACT_SERVICES", "*").upper().split(",")

# Whether to log all services to the file regardless of selected console services
LOG_ALL_TO_FILE = os.getenv("MIACT_LOG_ALL", "True").lower() in ("true", "1", "t")

# ── AI / Ollama ───────────────────────────────────────────────
AI_PROVIDER = os.getenv("AI_PROVIDER", "native") # "native" or "ollama"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL_INTENT = os.getenv("OLLAMA_MODEL_INTENT", "qwen2.5:0.5b")
OLLAMA_MODEL_SUMMARY = os.getenv("OLLAMA_MODEL_SUMMARY", "qwen2.5:0.5b")
