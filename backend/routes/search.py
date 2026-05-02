from fastapi import APIRouter
from backend.orchestrators.search_orchestrator import execute_search
from backend.utils.logger import logger
from backend.database.connection import get_connection, execute_query
import backend.config.variables as _vars

router = APIRouter()

@router.get("/db-status")
def db_status():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        execute_query(cursor, "SELECT COUNT(*) FROM entities")
        e_count = cursor.fetchone()[0]
        execute_query(cursor, "SELECT COUNT(*) FROM documents")
        d_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {"status": "connected", "entities": e_count, "documents": d_count}
    except Exception as e:
        logger.error("SEARCH", f"Database status check failed: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/clear-db")
def clear_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Truncate tables to clear all cache
        if _vars.DB_TYPE == "postgres":
            execute_query(cursor, "TRUNCATE TABLE facts, documents, entities, sources CASCADE")
        else:
            # SQLite doesn't support TRUNCATE or CASCADE
            tables = ["facts", "documents", "entities", "sources", "opinions", "queries", "sessions", "entity_aliases"]
            for table in tables:
                execute_query(cursor, f"DELETE FROM {table}")
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("SEARCH", "Database cache cleared manually via API.")
        return {"status": "success", "message": "Cache cleared successfully"}
    except Exception as e:
        logger.error("SEARCH", f"Failed to clear database cache: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/search")
async def search(query: str, t: str = None):
    # Delegate complex orchestration to the search_orchestrator
    return await execute_search(query, t)
