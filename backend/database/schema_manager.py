import psycopg2
from backend.database.connection import get_connection
from backend.utils.logger import logger
import backend.config.variables as _vars

SCHEMA_QUERIES = [
    """
    CREATE TABLE IF NOT EXISTS entities (
        entity_id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        entity_type TEXT,
        parent_id INT REFERENCES entities(entity_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sources (
        source_id SERIAL PRIMARY KEY,
        name TEXT,
        base_url TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        published_at TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS documents (
        document_id TEXT PRIMARY KEY,
        source_id INT REFERENCES sources(source_id),
        title TEXT,
        domain_type TEXT,
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS queries (
        query_id SERIAL PRIMARY KEY,
        session_id INT REFERENCES sessions(session_id),
        query_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS facts (
        fact_id SERIAL PRIMARY KEY,
        entity_id INT REFERENCES entities(entity_id),
        document_id TEXT REFERENCES documents(document_id),
        aspect TEXT NOT NULL,
        value TEXT,
        unit TEXT,
        attr_type TEXT,
        confidence_score FLOAT DEFAULT 1.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS opinions (
        opinion_id SERIAL PRIMARY KEY,
        entity_id INT REFERENCES entities(entity_id),
        document_id TEXT REFERENCES documents(document_id),
        aspect TEXT,
        opinion_text TEXT,
        sentiment_label TEXT,
        sentiment_score FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS entity_aliases (
        alias TEXT PRIMARY KEY,
        canonical TEXT
    );
    """
]

def initialize_db():
    """Create tables if they don't exist."""
    logger.info("DATABASE", "Initializing database schema...")
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        for query in SCHEMA_QUERIES:
            cur.execute(query)
        conn.commit()
        logger.info("DATABASE", "Database schema initialized successfully.")
        return True
    except Exception as e:
        logger.error("DATABASE", f"Failed to initialize database: {e}")
        if "password authentication failed" in str(e):
            logger.error("DATABASE", "CRITICAL: Check your DB_PASSWORD in the .env file.")
        return False
    finally:
        if conn:
            conn.close()

def drop_all_tables():
    """Delete all tables (reset database)."""
    logger.warning("DATABASE", "DROPPING ALL TABLES!")
    tables = ["opinions", "facts", "queries", "sessions", "documents", "sources", "entities", "entity_aliases"]
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        for table in tables:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
        conn.commit()
        logger.info("DATABASE", "All tables dropped successfully.")
        return True
    except Exception as e:
        logger.error("DATABASE", f"Failed to drop tables: {e}")
        return False
    finally:
        if conn:
            conn.close()

def check_connection():
    """Verify if database connection is possible."""
    try:
        conn = get_connection()
        conn.close()
        return True
    except Exception as e:
        logger.error("DATABASE", f"Connection check failed: {e}")
        return False
