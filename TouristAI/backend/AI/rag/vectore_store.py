# rag/vector_store.py
import os
from typing import Optional

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "rag", "restaurant_db")
)

embeddings = None
db = None
_db_mtime: Optional[float] = None
_embeddings_error: Optional[str] = None


def get_embeddings():
    """
    Lazily initializes HuggingFace embeddings.

    By default this uses local files only, so backend startup and chat requests do
    not hang on Hugging Face network timeouts. Set RAG_ALLOW_MODEL_DOWNLOAD=1 if
    you want the app to download the model when it is not already cached.
    """
    global embeddings, _embeddings_error

    if embeddings is not None:
        return embeddings
    if _embeddings_error is not None:
        return None

    allow_download = os.getenv("RAG_ALLOW_MODEL_DOWNLOAD", "0").lower() in {"1", "true", "yes"}
    model_kwargs = {} if allow_download else {"local_files_only": True}

    try:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name=MODEL_NAME,
            model_kwargs=model_kwargs,
        )
        return embeddings
    except Exception as e:
        _embeddings_error = str(e)
        mode = "download" if allow_download else "local cache"
        print(f"[WARNING] RAG embeddings unavailable from {mode}; skipping FAISS RAG. Error: {e}")
        return None


def get_db():
    """
    Lazily loads the FAISS database only after embeddings are available.
    """
    global db, _db_mtime

    index_path = os.path.join(DB_PATH, "index.faiss")
    index_mtime = os.path.getmtime(index_path) if os.path.exists(index_path) else None

    if db is not None and _db_mtime == index_mtime:
        return db

    embedding_model = get_embeddings()
    if embedding_model is None:
        return None

    try:
        from langchain_community.vectorstores import FAISS

        if os.path.exists(DB_PATH) and os.path.exists(index_path):
            db = FAISS.load_local(
                DB_PATH,
                embedding_model,
                allow_dangerous_deserialization=True,
            )
            _db_mtime = index_mtime
    except Exception as e:
        print(f"[WARNING] Failed to load FAISS database at {DB_PATH}: {e}")
        db = None
        _db_mtime = None

    return db
