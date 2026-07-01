# rag/vector_store.py

import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

DB_PATH = "rag/restaurant_db"

db = None

if os.path.exists(os.path.join(DB_PATH, "index.faiss")):
    db = FAISS.load_local(
        DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True,
    )
    print("✅ Loaded existing vector DB.")
else:
    print("⚠️ Vector DB does not exist. It will be created when the first document is added.")