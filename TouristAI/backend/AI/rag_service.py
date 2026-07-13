import os
from groq import Groq
from langchain_community.vectorstores import FAISS
import rag.vectore_store as vector_store
from dotenv import load_dotenv

import threading

load_dotenv()

db_lock = threading.Lock()
print("GROQ KEY =", os.getenv("GROQ_API_KEY"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def load_db():
    """
    Load FAISS database if it exists.
    """
    if os.path.exists(vector_store.DB_PATH):
        return FAISS.load_local(
            vector_store.DB_PATH,
            vector_store.embeddings,
            allow_dangerous_deserialization=True
        )

    return None


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

        if vector_store.db is None:
            vector_store.db = FAISS.from_texts(
                [question],
                vector_store.embeddings,
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


def call_groq(question):

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
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
        save_to_rag(question, answer)

    return {
        "answer": answer,
        "source": "Groq"
    }