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
