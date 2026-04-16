import psycopg2
import backend.config.variables as _vars

def get_connection():
    """
    Creates and returns a connection to the PostgreSQL database
    using parameters defined in config/variables.py.
    """
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
