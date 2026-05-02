import psycopg2
import sqlite3
from backend.database.connection import get_connection, execute_query
from backend.utils.logger import logger
import backend.config.variables as _vars

SCHEMA_QUERIES = [
    """
    CREATE TABLE IF NOT EXISTS entities (
        entity_id {pk_type},
        name TEXT UNIQUE NOT NULL,
        entity_type TEXT,
        parent_id INT REFERENCES entities(entity_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sources (
        source_id {pk_type},
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
        session_id {pk_type},
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS queries (
        query_id {pk_type},
        session_id INT REFERENCES sessions(session_id),
        query_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS facts (
        fact_id {pk_type},
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
        opinion_id {pk_type},
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
    logger.info("DATABASE", f"Initializing database schema for {_vars.DB_TYPE}...")
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        pk_type = "SERIAL PRIMARY KEY"
        if _vars.DB_TYPE == "sqlite":
            pk_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
            
        for query_template in SCHEMA_QUERIES:
            query = query_template.format(pk_type=pk_type)
            execute_query(cur, query)
            
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
            cascade = " CASCADE" if _vars.DB_TYPE == "postgres" else ""
            execute_query(cur, f"DROP TABLE IF EXISTS {table}{cascade};")
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
