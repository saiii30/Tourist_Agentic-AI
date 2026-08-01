# backend/AI/rag/rag_admin.py
import argparse
import os
import sys
from collections import Counter, defaultdict

AI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if AI_DIR not in sys.path:
    sys.path.append(AI_DIR)

from rag.service import rag_service  # noqa: E402
from rag.vectore_store import get_db  # noqa: E402


def iter_documents():
    db = get_db()
    if db is None:
        raise RuntimeError("FAISS database unavailable. Check embeddings and RAG dependencies.")
    return list(getattr(db.docstore, "_dict", {}).values())


def print_stats() -> None:
    docs = iter_documents()
    by_source = Counter()
    by_city = Counter()
    by_knowledge_type = Counter()
    by_source_type = Counter()

    for doc in docs:
        meta = doc.metadata or {}
        by_source[meta.get("source_domain") or meta.get("source_url") or "Unknown"] += 1
        by_city[meta.get("city") or "Unknown"] += 1
        by_knowledge_type[meta.get("knowledge_type") or "unspecified"] += 1
        by_source_type[meta.get("source_type") or "unspecified"] += 1

    print(f"Total chunks: {len(docs)}")
    print("\nBy knowledge_type:")
    for name, count in by_knowledge_type.most_common():
        print(f"- {name}: {count}")

    print("\nBy source_type:")
    for name, count in by_source_type.most_common():
        print(f"- {name}: {count}")

    print("\nBy city:")
    for name, count in by_city.most_common(20):
        print(f"- {name}: {count}")

    print("\nTop sources:")
    for name, count in by_source.most_common(20):
        print(f"- {name}: {count}")


def print_sources() -> None:
    grouped = defaultdict(lambda: {"count": 0, "cities": set(), "knowledge_types": set(), "url": ""})
    for doc in iter_documents():
        meta = doc.metadata or {}
        key = meta.get("source_domain") or meta.get("source_url") or "Unknown"
        grouped[key]["count"] += 1
        grouped[key]["cities"].add(meta.get("city") or "Unknown")
        grouped[key]["knowledge_types"].add(meta.get("knowledge_type") or "unspecified")
        grouped[key]["url"] = meta.get("source_url") or grouped[key]["url"]

    for name, info in sorted(grouped.items(), key=lambda item: item[0].lower()):
        cities = ", ".join(sorted(info["cities"]))
        knowledge_types = ", ".join(sorted(info["knowledge_types"]))
        print(f"- {name}")
        print(f"  chunks: {info['count']}")
        print(f"  cities: {cities}")
        print(f"  knowledge: {knowledge_types}")
        print(f"  url: {info['url']}")


def test_query(query: str, city: str, top_k: int) -> None:
    result = rag_service.query_rag(query, city=city, top_k=top_k)
    print(f"Has knowledge: {result.get('has_knowledge')}")
    print(f"Intent: {result.get('rag_intent')}")
    print(f"City: {result.get('city')}")
    print("\nAnswer:")
    print(result.get("answer_text") or result.get("context_text") or "No answer")

    print("\nCitations:")
    for citation in result.get("citations", []):
        print(f"- {citation.get('source_name')} | {citation.get('trust_score')}")
        print(f"  {citation.get('source_url')}")

    print("\nRaw chunks:")
    for item in result.get("raw_results", [])[:top_k]:
        print(
            f"- {item.get('chunk_id')} | {item.get('city')} | "
            f"{item.get('destination')} | {item.get('category')} | score={item.get('relevance_score')}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect and test TouristAI RAG.")
    parser.add_argument("--stats", action="store_true", help="Print vector store summary stats.")
    parser.add_argument("--sources", action="store_true", help="List indexed sources.")
    parser.add_argument("--query", help="Run a RAG test query.")
    parser.add_argument("--city", default="Madurai", help="City/destination context for --query.")
    parser.add_argument("--top-k", type=int, default=4, help="Number of chunks to inspect for --query.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.stats:
        print_stats()
        return 0
    if args.sources:
        print_sources()
        return 0
    if args.query:
        test_query(args.query, args.city, args.top_k)
        return 0

    print("Choose one: --stats, --sources, or --query \"...\"")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
