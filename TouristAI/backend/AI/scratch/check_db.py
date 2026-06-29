import sys
import os

# Add AI folder to sys.path to find rag_service correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_service import load_db

db = load_db()
if db:
    print("FAISS RAG DB loaded successfully!")
    print(f"Total Cached Questions: {len(db.docstore._dict)}\n")
    
    for idx, (doc_id, doc) in enumerate(db.docstore._dict.items(), 1):
        print(f"[{idx}] Cached Question:")
        print(f"    {doc.page_content.strip()}")
        ans = doc.metadata.get("answer", "None").strip()
        # Print a short preview of the cached answer
        ans_preview = ans[:300] + "..." if len(ans) > 300 else ans
        print(f"    Answer Preview:")
        print(f"    {ans_preview}")
        print("-" * 60)
else:
    print("No FAISS RAG DB index found.")
