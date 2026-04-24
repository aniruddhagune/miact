import sys
import os

# Ensure backend is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.database.schema_manager import initialize_db, drop_all_tables, check_connection
from backend.utils.logger import logger

def main():
    if len(sys.argv) < 2:
        print("\n🛠️ MIACT Database Manager")
        print("Usage:")
        print("  python manage_db.py init    - Create tables if they don't exist")
        print("  python manage_db.py reset   - Drop all tables and recreate them")
        print("  python manage_db.py check   - Check database connection")
        return

    cmd = sys.argv[1].lower()

    if cmd == "init":
        print("🚀 Initializing database...")
        success = initialize_db()
        if success:
            print("✅ Database is ready.")
        else:
            print("❌ Initialization failed. Check backend/debug/ logs.")

    elif cmd == "reset":
        confirm = input("⚠️ This will DELETE ALL DATA in the database. Are you sure? (y/n): ")
        if confirm.lower() == 'y':
            print("🧹 Dropping tables...")
            if drop_all_tables():
                print("🚀 Re-initializing...")
                if initialize_db():
                    print("✅ Database reset successful.")
                else:
                    print("❌ Re-initialization failed.")
            else:
                print("❌ Failed to drop tables.")
        else:
            print("Operation cancelled.")

    elif cmd == "check":
        print("🔍 Checking connection...")
        import backend.config.variables as _vars
        print(f"   Target DB: {_vars.DB_NAME}")
        print(f"   User:      {_vars.DB_USER}")
        print(f"   Host:      {_vars.DB_HOST}")
        print(f"   Port:      {_vars.DB_PORT}")
        # Print first 2 chars of password to verify it's not empty/default
        pw = _vars.DB_PASSWORD
        pw_hint = (pw[:2] + "*" * (len(pw)-2)) if pw else "[EMPTY]"
        print(f"   Password:  {pw_hint}")

        if check_connection():
            print("✅ Connection successful.")
        else:
            print("❌ Connection failed. Check your .env file and ensure Postgres is running.")

    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
