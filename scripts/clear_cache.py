from backend.database.connection import get_connection, execute_query
import backend.config.variables as _vars

def clear_bad_aliases():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        if _vars.DB_TYPE == "sqlite":
            execute_query(cursor, "SELECT name FROM sqlite_master WHERE type='table' AND name='entity_aliases'")
        else:
            execute_query(cursor, "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'entity_aliases')")
        
        exists = cursor.fetchone()
        if exists and exists[0]:
            print("Cleaning entity_aliases table...")
            # Remove anything that doesn't look like a product or was mis-resolved
            execute_query(cursor, "DELETE FROM entity_aliases WHERE canonical LIKE '%gsmarena.com%' OR alias IN ('narendra modi', 'donald trump')")
            conn.commit()
            print("Done.")
        else:
            print("entity_aliases table does not exist.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clear_bad_aliases()
