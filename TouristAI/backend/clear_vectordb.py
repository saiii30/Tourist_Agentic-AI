import os

def clear_vector_database():
    """
    Deletes the FAISS vector database files from the disk.
    This function looks for 'faiss_index.bin' and 'faiss_index.pkl'
    in the current directory and deletes them if they exist.
    """
    # Assuming the vector DB files are in the same directory as this script.
    # The vector DB files are likely created by rag_service.py inside the AI directory.
    # Let's build a robust path to that directory.
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

if __name__ == "__main__":
    # This allows you to run the script directly from the command line.
    print("--- Clearing Vector Database ---")
    clear_vector_database()
    print("--- Operation Complete ---")