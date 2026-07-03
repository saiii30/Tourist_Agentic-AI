import os

def clear_vector_database():
    """
    Deletes the FAISS vector database files from the disk.
    This function looks for 'index.faiss' and 'index.pkl'
    in the vector store directory and deletes them if they exist.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_directory = os.path.join(script_dir, "AI", "rag", "restaurant_db")

    index_file = os.path.join(db_directory, "index.faiss")
    metadata_file = os.path.join(db_directory, "index.pkl")

    print(f"Searching for vector database files in: {db_directory}")

    if os.path.exists(index_file):
        os.remove(index_file)
        print(f"✅ Deleted vector index: {index_file}")
    else:
        print(f"ℹ️ Vector index file not found at: {index_file}")

    if os.path.exists(metadata_file):
        os.remove(metadata_file)
        print(f"✅ Deleted vector metadata: {metadata_file}")
    else:
        print(f"ℹ️ Vector metadata file not found at: {metadata_file}")

def clear_sqlite_databases():
    """
    Deletes the SQLite database files from the disk.
    This function looks for 'tourist_ai.db' and 'chat.db' and deletes them.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to tourist_ai.db (in backend/)
    tourist_db_path = os.path.join(script_dir, "tourist_ai.db")
    
    # Path to chat.db (in backend/AI/)
    chat_db_path = os.path.join(script_dir, "AI", "chat.db")

    print(f"\nSearching for SQLite database files...")

    if os.path.exists(tourist_db_path):
        os.remove(tourist_db_path)
        print(f"✅ Deleted SQLite database: {tourist_db_path}")
    else:
        print(f"ℹ️ SQLite database not found at: {tourist_db_path}")

    if os.path.exists(chat_db_path):
        os.remove(chat_db_path)
        print(f"✅ Deleted SQLite database: {chat_db_path}")
    else:
        print(f"ℹ️ SQLite database not found at: {chat_db_path}")


if __name__ == "__main__":
    # This allows you to run the script directly from the command line.
    print("--- Clearing All Databases ---")
    clear_vector_database()
    clear_sqlite_databases()
    print("--- Operation Complete ---")