import psycopg2
import sqlite3
import backend.config.variables as _vars

def get_connection():
    """
    Creates and returns a connection to the database
    based on the DB_TYPE defined in config/variables.py.
    """
    if _vars.DB_TYPE == "sqlite":
        conn = sqlite3.connect(_vars.SQLITE_PATH)
        # Enable foreign keys for SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    else:
        return psycopg2.connect(
            dbname=_vars.DB_NAME,
            user=_vars.DB_USER,
            password=_vars.DB_PASSWORD,
            host=_vars.DB_HOST,
            port=_vars.DB_PORT
        )

def get_db():
    """Alias for get_connection, used in some routes."""
    return get_connection()

def execute_query(cursor, query, params=None):
    """
    Helper to execute a query, handling placeholder differences between 
    PostgreSQL (%s) and SQLite (?).
    """
    if _vars.DB_TYPE == "sqlite":
        query = query.replace("%s", "?")
    
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
