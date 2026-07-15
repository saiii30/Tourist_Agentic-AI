# rag/vector_store.py
import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

DB_PATH = "rag/restaurant_db"

try:
    if os.path.exists(DB_PATH) and os.path.exists(os.path.join(DB_PATH, "index.faiss")):
        db = FAISS.load_local(
            DB_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
    else:
        db = None
except Exception as e:
    print(f"[WARNING] Failed to load FAISS database at {DB_PATH}: {e}")
    db = None