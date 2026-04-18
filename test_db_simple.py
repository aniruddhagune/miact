import psycopg2
import os
from dotenv import load_dotenv

# Load your current .env
load_dotenv()

def test_manual_check():
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")

    print(f"--- Attempting Connection with .env details ---")
    print(f"DB: {db_name} | User: {db_user} | Host: {db_host}")
    
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        print("\n✅ SUCCESS: Connection established!")
        conn.close()
    except psycopg2.OperationalError as e:
        print("\n❌ FAILED")
        if "password authentication failed" in str(e):
            print("REASON: Your password in .env is WRONG.")
        elif "does not exist" in str(e):
            print(f"REASON: The database '{db_name}' doesn't exist yet.")
            print(f"ACTION: Try connecting to dbname='postgres' instead to see if that works.")
        else:
            print(f"REASON: {e}")

if __name__ == "__main__":
    test_manual_check()
