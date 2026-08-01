# backend/AI/rag/admin_ingest.py
"""
Safely ingest official tourism website pages into the TouristAI RAG store.

Default behavior is merge-only: existing FAISS knowledge remains in place and
new official-source chunks are added. Use --replace only for an intentional
full rebuild.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from io import BytesIO
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document

AI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if AI_DIR not in sys.path:
    sys.path.append(AI_DIR)

from rag.vectore_store import DB_PATH, get_embeddings  # noqa: E402
from rag.knowledge_taxonomy import SOURCE_TYPES, normalize_knowledge_type, normalize_source_type  # noqa: E402

try:
    from rag.seed_rag_knowledge import OFFICIAL_TOURISM_DOCUMENTS
except Exception:
    OFFICIAL_TOURISM_DOCUMENTS = []


DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_CHUNK_SIZE = 1100
DEFAULT_CHUNK_OVERLAP = 180
USER_AGENT = "TouristAI-RAG-Admin/1.0 (+official tourism ingestion)"

BOILERPLATE_PATTERNS = [
    r"share on facebook",
    r"share on x",
    r"formaly twitter",
    r"skip to main content",
    r"screen reader access",
    r"change this anytime using the language dropdown",
    r"we would love to hear your suggestions",
    r"feedback at info\[dot\]",
    r"copyright",
    r"all rights reserved",
]

PDF_SOURCE_TYPES = {"pdf_brochure", "tourism_board_pdf", "government_brochure", "state_tourism_document"}


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    return text


def source_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def stable_chunk_id(url: str, index: int, text: str) -> str:
    digest = hashlib.sha1(f"{url}|{index}|{text[:180]}".encode("utf-8")).hexdigest()
    return f"official_{digest[:16]}"


def load_sources(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict):
        payload = payload.get("sources", [])

    if not isinstance(payload, list):
        raise ValueError("Source file must be a JSON list or an object with a 'sources' list.")

    sources = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        if item.get("enabled", True) is False:
            continue
        if not item.get("url") and not item.get("file_path"):
            continue
        sources.append(item)

    return sources

def is_boilerplate(text: str) -> bool:
    lower = text.lower()
    if any(re.search(pattern, lower) for pattern in BOILERPLATE_PATTERNS):
        return True
    if len(set(lower.split())) <= 3 and len(lower) < 60:
        return True
    return False


def extract_page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        tag.decompose()

    candidates = []
    for tag in soup.find_all(["h1", "h2", "h3", "p", "li", "td"]):
        text = normalize_text(tag.get_text(" "))
        min_len = 12 if tag.name in {"h1", "h2", "h3"} else 35
        if len(text) >= min_len and not is_boilerplate(text):
            candidates.append(text)

    deduped = []
    seen = set()
    for text in candidates:
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(text)

    return "\n\n".join(deduped)


def extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF ingestion requires pypdf. Install backend requirements first.") from exc

    reader = PdfReader(BytesIO(content))
    pages = []
    for idx, page in enumerate(reader.pages, start=1):
        text = normalize_text(page.extract_text() or "")
        if text and not is_boilerplate(text):
            pages.append(f"Page {idx}: {text}")
    return "\n\n".join(pages)


def extract_plain_text(content: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current = ""

    for paragraph in paragraphs:
        if not current:
            current = paragraph
            continue

        if len(current) + len(paragraph) + 2 <= chunk_size:
            current = f"{current}\n\n{paragraph}"
        else:
            chunks.append(current)
            tail = current[-overlap:] if overlap > 0 else ""
            current = f"{tail}\n\n{paragraph}" if tail else paragraph

    if current:
        chunks.append(current)

    return [chunk for chunk in chunks if len(chunk) >= 80 and not is_boilerplate(chunk)]


def is_pdf_source(source: Dict[str, Any], content_type: str = "") -> bool:
    url = str(source.get("url") or source.get("file_path") or "").lower()
    source_type = normalize_source_type(source.get("source_type"))
    return url.endswith(".pdf") or source_type in PDF_SOURCE_TYPES or "application/pdf" in content_type.lower()


def fetch_source_content(source: Dict[str, Any]) -> tuple[bytes, str, str]:
    file_path = source.get("file_path")
    if file_path:
        with open(file_path, "rb") as handle:
            content = handle.read()
        return content, "application/pdf" if str(file_path).lower().endswith(".pdf") else "text/plain", file_path

    url = source["url"]
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(
        url,
        headers=headers,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        allow_redirects=True,
    )
    response.raise_for_status()
    return response.content, response.headers.get("content-type", ""), response.url


def crawl_source(source: Dict[str, Any], chunk_size: int, overlap: int) -> List[Document]:
    source_ref = source.get("url") or source.get("file_path")
    content, content_type, final_ref = fetch_source_content(source)

    if is_pdf_source(source, content_type):
        page_text = extract_pdf_text(content)
    elif "text/plain" in content_type.lower() or str(final_ref).lower().endswith((".txt", ".md")):
        page_text = extract_plain_text(content)
    else:
        page_text = extract_page_text(extract_plain_text(content))

    if not page_text:
        return []

    chunks = chunk_text(page_text, chunk_size=chunk_size, overlap=overlap)
    stored_source_url = final_ref if str(final_ref).startswith("http") else str(source_ref)
    domain = source.get("source_domain") or source.get("name") or source_domain(stored_source_url if stored_source_url.startswith("http") else "")
    destination = source.get("destination") or source.get("city") or "India"
    city = source.get("city") or source.get("destination") or "India"
    category = source.get("category") or "Official Tourism"
    knowledge_type = normalize_knowledge_type(source.get("knowledge_type"), category)
    source_type = normalize_source_type(source.get("source_type"))
    trust_score = int(source.get("trust_score") or SOURCE_TYPES.get(source_type, 100))

    documents = []
    for index, chunk in enumerate(chunks):
        chunk_id = stable_chunk_id(str(source_ref), index, chunk)
        documents.append(
            Document(
                page_content=(
                    f"[{category} | {destination}]\n\n"
                    f"{chunk}"
                ),
                metadata={
                    "chunk_id": chunk_id,
                    "destination": destination,
                    "city": city,
                    "category": category,
                    "knowledge_type": knowledge_type,
                    "source_type": source_type,
                    "source_domain": domain,
                    "source_url": stored_source_url,
                    "trust_score": trust_score,
                    "language": source.get("language", "en"),
                    "is_official_tourism_source": True,
                    "content_format": "pdf" if is_pdf_source(source, content_type) else "html",
                    "ingested_at": time.strftime("%Y-%m-%d"),
                },
            )
        )

    return documents


def unique_documents(documents: Iterable[Document]) -> List[Document]:
    seen = set()
    unique = []
    for doc in documents:
        key = doc.metadata.get("chunk_id") or hashlib.sha1(doc.page_content.encode("utf-8")).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        unique.append(doc)
    return unique


def index_documents(documents: List[Document], replace: bool) -> None:
    from langchain_community.vectorstores import FAISS

    embedding_model = get_embeddings()
    if embedding_model is None:
        raise RuntimeError(
            "Embedding model unavailable. Install RAG dependencies and set "
            "RAG_ALLOW_MODEL_DOWNLOAD=1 for the first model download if needed."
        )

    os.makedirs(DB_PATH, exist_ok=True)
    has_existing_index = os.path.exists(os.path.join(DB_PATH, "index.faiss"))

    if replace or not has_existing_index:
        db = FAISS.from_documents(documents, embedding_model)
    else:
        db = FAISS.load_local(
            DB_PATH,
            embedding_model,
            allow_dangerous_deserialization=True,
        )
        db.add_documents(documents)

    db.save_local(DB_PATH)


def build_documents(args: argparse.Namespace) -> List[Document]:
    sources = load_sources(args.sources)
    documents: List[Document] = []

    if args.include_seeded:
        documents.extend(OFFICIAL_TOURISM_DOCUMENTS)

    for source in sources:
        url = source.get("url") or source.get("file_path")
        try:
            source_docs = crawl_source(source, args.chunk_size, args.overlap)
            documents.extend(source_docs)
            print(f"[OK] {url} -> {len(source_docs)} chunks")
        except Exception as exc:
            print(f"[WARN] Failed to ingest {url}: {exc}")

    return unique_documents(documents)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest official tourism websites into TouristAI RAG.")
    parser.add_argument(
        "--sources",
        required=True,
        help="Path to a JSON source registry.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace the FAISS store instead of merging. Use carefully.",
    )
    parser.add_argument(
        "--include-seeded",
        action="store_true",
        help="Include curated built-in official RAG documents during this ingestion.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Crawl and report chunks without saving to FAISS.",
    )
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    documents = build_documents(args)

    if not documents:
        print("[ERROR] No documents were created. FAISS store was not changed.")
        return 1

    print(f"[INFO] Prepared {len(documents)} unique documents.")

    if args.dry_run:
        print("[DRY RUN] FAISS store was not changed.")
        return 0

    index_documents(documents, replace=args.replace)
    mode = "replaced" if args.replace else "merged"
    print(f"[SUCCESS] {mode} {len(documents)} documents into FAISS at {DB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
