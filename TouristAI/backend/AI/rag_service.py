import os
from groq import Groq
import rag.vectore_store as vector_store
from dotenv import load_dotenv

import threading

load_dotenv()

db_lock = threading.Lock()


class LazyGroqClient:
    """Create the Groq SDK client only when an AI operation needs it.

    Keeping this lazy allows the API server, health routes, cached trips, and
    non-Groq features to start when GROQ_API_KEY has not been configured.
    """

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            api_key = os.getenv("GROQ_API_KEY", "").strip()
            if not api_key:
                raise RuntimeError(
                    "GROQ_API_KEY is not configured. Add it to the project .env "
                    "before using Groq-powered AI features."
                )
            self._client = Groq(api_key=api_key)
        return self._client

    def __getattr__(self, name):
        return getattr(self._get_client(), name)


client = LazyGroqClient()


def load_db():
    """
    Load FAISS database if it exists.
    """
    return vector_store.get_db()


def search_data(question):
    """
    First check exact match.
    Then check semantic match.
    """

    try:
        db = load_db()

        if db is None:
            return None

        docs = db.similarity_search_with_score(
            question,
            k=3
        )

        if not docs:
            return None

        for doc, score in docs:

            print("Question :", question)
            print("Matched  :", doc.page_content)
            print("Score    :", score)

            # Exact Match
            if (
                doc.page_content.lower().strip()
                ==
                question.lower().strip()
            ):
                print("Exact Match Found")
                return doc.metadata.get("answer")

            # Semantic Match
            if score < 0.20:
                print("Semantic Match Found")
                return doc.metadata.get("answer")

        return None

    except Exception as e:
        print("Search Error :", e)
        return None


def save_to_rag(question, answer):

    with db_lock:
        embeddings = vector_store.get_embeddings()
        if embeddings is None:
            print("[INFO] RAG save skipped because embeddings are unavailable.")
            return False
        try:
            from langchain_community.vectorstores import FAISS
        except Exception as e:
            print(f"[INFO] RAG save skipped because FAISS is unavailable: {e}")
            return False

        if vector_store.db is None:
            vector_store.db = FAISS.from_texts(
                [question],
                embeddings,
                metadatas=[{"answer": answer}]
            )
        else:
            vector_store.db.add_texts(
                [question],
                metadatas=[{"answer": answer}]
            )

        vector_store.db.save_local(
            vector_store.DB_PATH
        )

        print("Saved to RAG")
        return True


def call_groq(question):

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return response.choices[0].message.content

def get_answer(question, check_rag_only=False):
    """
    If check_rag_only=True:
        Search only in RAG.

    If check_rag_only=False:
        Skip RAG and directly call Groq.
    """

    if check_rag_only:
        rag_answer = search_data(question)

        if rag_answer:
            print("Answer from RAG")
            return {
                "answer": rag_answer,
                "source": "RAG"
            }

        return None

    print("Skipping RAG. Calling Groq.")

    answer = call_groq(question)

    if answer:
        try:
            save_to_rag(question, answer)
        except Exception as e:
            print(f"[WARNING] Could not save Groq answer to RAG: {e}")

    return {
        "answer": answer,
        "source": "Groq"
    }
