import os
import shutil
import psycopg2
from dotenv import load_dotenv

# Load env variables
script_dir = os.path.dirname(os.path.abspath(__file__))
# Check backend/.env or backend/AI/.env or root .env
for env_path in [
    os.path.join(script_dir, ".env"),
    os.path.join(os.path.dirname(script_dir), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(script_dir)), ".env")
]:
    if os.path.exists(env_path):
        load_dotenv(env_path)

def cleanup_postgres():
    print("Cleaning up PostgreSQL database...")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    db_name = os.getenv("DB_NAME", "tourist_ai")

    conn = None
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            dbname=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()

        tables = [
            "users", "trips", "itineraries", "trip_details", "trip_versions", 
            "calendar_events", "sync_logs", "places", "guided_trip_state", 
            "agent_sessions", "agent_session_state"
        ]
        for table in tables:
            try:
                # Truncate table data and reset serial identity columns (CASCADE handles dependencies)
                cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                print(f"  [OK] Cleared PostgreSQL table: {table}")
            except Exception as e:
                print(f"  [WARNING] Could not clear table {table} (it might not exist yet): {e}")

        cursor.close()
        print("PostgreSQL cleanup completed successfully.")
    except Exception as e:
        print(f"Error connecting to or modifying PostgreSQL: {e}")
    finally:
        if conn:
            conn.close()

def cleanup_rag():
    print("Cleaning up RAG (FAISS) vector database...")
    paths_to_check = [
        os.path.join(script_dir, "rag", "restaurant_db"),
        os.path.join(script_dir, "rag", "hotel_db"),
        os.path.join(os.path.dirname(script_dir), "AI", "rag", "restaurant_db"),
    ]
    
    cleaned = False
    for path in paths_to_check:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path) and os.path.isdir(abs_path):
            try:
                shutil.rmtree(abs_path)
                print(f"  [OK] Removed RAG directory at: {abs_path}")
                cleaned = True
            except Exception as e:
                print(f"  [WARNING] Error removing RAG directory at {abs_path}: {e}")
                
    if not cleaned:
        print("  [INFO] No active RAG directories found to delete.")
    else:
        print("RAG database cleanup completed successfully.")

def cleanup_sqlite():
    print("Cleaning up local SQLite database...")
    sqlite_path = os.path.abspath(os.path.join(script_dir, "tourist_ai.db"))
    if not os.path.exists(sqlite_path):
        sqlite_path = os.path.abspath(os.path.join(os.path.dirname(script_dir), "tourist_ai.db"))
        
    if os.path.exists(sqlite_path):
        try:
            os.remove(sqlite_path)
            print(f"  [OK] Removed SQLite database at: {sqlite_path}")
        except Exception as e:
            print(f"  [WARNING] Error removing SQLite database: {e}")
    else:
        print("  [INFO] No SQLite database found to delete.")

if __name__ == "__main__":
    print("==========================================")
    print("      TOURIST AI DATA CLEANUP SCRIPT      ")
    print("==========================================")
    cleanup_postgres()
    print("-" * 42)
    cleanup_rag()
    print("-" * 42)
    cleanup_sqlite()
    print("==========================================")
    print("All requested data cleanups are finished!")
