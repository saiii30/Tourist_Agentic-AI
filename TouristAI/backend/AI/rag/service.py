# backend/AI/rag/service.py
import json
import re
from typing import List, Dict, Any, Optional
from .schemas import RAGSearchResult, CollectionType
from .knowledge_router import KnowledgeRouter
from .vectore_store import get_db
from .official_fallback import build_official_fallback, infer_requested_destination
from .image_assets import get_rag_image_url, get_rag_image_urls

STOPWORDS = {
    "what", "is", "the", "for", "in", "a", "an", "of", "to", "and", "or",
    "are", "with", "while", "visiting", "visit", "tell", "about", "explain"
}

OFFICIAL_SOURCE_TERMS = {
    "incredible india",
    "tamil nadu tourism",
    "district",
    "district administration",
    "asi",
    "archaeological survey",
    "official tourism",
    "official website",
}

KNOWN_DESTINATION_CITIES = {
    "kanyakumari": "Kanniyakumari",
    "kanniyakumari": "Kanniyakumari",
    "ooty": "Ooty",
    "nilgiris": "Ooty",
    "kodaikanal": "Kodaikanal",
    "madurai": "Madurai",
    "salem": "Salem",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "uttar pradesh": "Uttar Pradesh",
    "rajasthan": "Rajasthan",
    "tamil nadu": "Tamil Nadu",
    "tamilnadu": "Tamil Nadu",
}

RAG_COVERED_CITIES = {
    "Madurai",
    "Tamil Nadu",
    "Kanniyakumari",
    "Ooty",
    "Kodaikanal",
    "Delhi",
    "Uttar Pradesh",
    "Rajasthan",
}

GENERATED_TRIP_PATTERNS = [
    r"\bplan a \d+[- ]?day trip\b",
    r"\btravel style is\b",
    r"\btravelers is\b",
    r"\bbudget is\b",
    r"\binterests are\b",
]

def query_terms(query: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-z0-9]+", query.lower())
        if len(term) > 2 and term not in STOPWORDS
    }

def looks_like_generated_trip_prompt(text: str) -> bool:
    lower = text.lower()
    return any(re.search(pattern, lower) for pattern in GENERATED_TRIP_PATTERNS)

def is_verified_knowledge_chunk(meta: Dict[str, Any], text: str) -> bool:
    return bool(
        meta.get("source_url")
        and meta.get("source_domain")
        and meta.get("chunk_id")
        and not looks_like_generated_trip_prompt(text)
    )

def detect_query_intent(query: str) -> Optional[str]:
    lower = query.lower()
    if "best time" in lower or "best season" in lower or "when to visit" in lower:
        return "best_time"
    if "how to reach" in lower or "directions" in lower or "nearest airport" in lower or "nearest railway" in lower:
        return "how_to_reach"
    if "history" in lower or "heritage" in lower or "built by" in lower:
        return "history"
    if "culture" in lower or "festival" in lower or "famous for" in lower or "known for" in lower:
        return "culture"
    if (
        "places to visit" in lower
        or "things to do" in lower
        or "attractions" in lower
        or "sightseeing" in lower
        or "nearby places" in lower
    ):
        return "destination_guide"
    if lower.startswith(("tell me about", "tell about", "explain")) and any(term in lower for term in KNOWN_DESTINATION_CITIES):
        return "official_source"
    if "asi" in lower or "archaeological survey" in lower:
        return "official_source"
    if "tourist spot" in lower or "tourist spots" in lower:
        return "official_source"
    if (
        ("tourist places" in lower or "places listed" in lower or "listed by" in lower or "monuments listed" in lower)
        and ("district" in lower or "official" in lower or "website" in lower or "tamil nadu tourism" in lower or "asi" in lower)
    ):
        return "listed_places"
    if any(term in lower for term in OFFICIAL_SOURCE_TERMS) or lower.startswith("what does "):
        return "official_source"
    if "dress" in lower or "attire" in lower or "clothing" in lower:
        return "dress"
    if "photography" in lower or "camera" in lower or "photo" in lower or "mobile" in lower:
        return "photography"
    if "timing" in lower or "opening hour" in lower or "open" in lower or "closed" in lower:
        return "timings"
    if "entry fee" in lower or "ticket" in lower or "darshan" in lower or "cost" in lower:
        return "fees"
    if "emergency" in lower or "helpline" in lower or "hospital" in lower or "police" in lower:
        return "emergency"
    if "permit" in lower or "safety" in lower or "rule" in lower or "custom" in lower:
        return "rules"
    return None

INTENT_REQUIRED_TERMS = {
    "listed_places": {"tourist", "places", "palace", "temple", "museum", "kovil", "teppakulam"},
    "official_source": {"tourism", "tourist", "places", "temple", "museum", "district", "india", "tamil", "nadu", "kanyakumari", "kanniyakumari", "ooty", "kodaikanal"},
    "dress": {"dress", "attire", "dhoti", "saree", "salwar", "footwear"},
    "photography": {"photography", "camera", "mobile", "electronics", "lockers"},
    "timings": {"timings", "open", "closed", "hours", "daily"},
    "fees": {"entry", "fees", "ticket", "darshan", "cost"},
    "emergency": {"emergency", "helpline", "hospital", "police", "ambulance"},
    "rules": {"rules", "customs", "guidelines", "permit", "safety"},
    "best_time": {"best", "time", "season", "visit", "weather", "months"},
    "how_to_reach": {"reach", "airport", "railway", "station", "road", "bus", "distance"},
    "history": {"history", "heritage", "built", "museum", "monument", "temple"},
    "culture": {"culture", "festival", "famous", "known", "food", "art"},
    "destination_guide": {"places", "attractions", "sightseeing", "tourist", "things", "visit", "guide"},
}

def matches_query_intent(query_intent: Optional[str], text: str, meta: Dict[str, Any]) -> bool:
    if not query_intent:
        return True

    haystack = f"{meta.get('category', '')} {meta.get('chunk_id', '')} {text}".lower()
    required_terms = INTENT_REQUIRED_TERMS.get(query_intent, set())
    return any(term in haystack for term in required_terms)

def source_preference(query: str) -> Optional[str]:
    lower = query.lower()
    if "kanyakumari" in lower or "kanniyakumari" in lower:
        return "kanniyakumari.nic.in"
    if "ooty" in lower or "nilgiris" in lower:
        return "nilgiris.nic.in"
    if "kodaikanal" in lower or "dindigul" in lower:
        return "dindigul.nic.in"
    if "delhi" in lower or "new delhi" in lower:
        return "/en/delhi"
    if "uttar pradesh" in lower:
        return "/en/uttar-pradesh"
    if "rajasthan" in lower:
        return "/en/rajasthan"
    if "incredible india" in lower:
        return "incredibleindia"
    if "asi" in lower or "archaeological survey" in lower:
        return "asi"
    if "district" in lower or "district administration" in lower:
        return ".nic.in"
    if "tamil nadu tourism" in lower:
        return "tamilnadutourism"
    return None

def infer_city_from_query(query: str, fallback: str = "Madurai") -> str:
    lower = (query or "").lower()
    for term, city in KNOWN_DESTINATION_CITIES.items():
        if term in lower:
            return city
    requested = infer_requested_destination(query)
    if requested:
        return requested
    return fallback

def is_city_covered(city: str) -> bool:
    clean = (city or "").strip()
    return clean in RAG_COVERED_CITIES

def matches_source_preference(query: str, meta: Dict[str, Any]) -> bool:
    preferred = source_preference(query)
    if not preferred:
        return True

    haystack = f"{meta.get('source_url', '')} {meta.get('source_domain', '')}".lower()
    if preferred == "asi":
        return "asi.nic.in" in haystack or "archaeological survey" in haystack
    if preferred == ".nic.in":
        return ".nic.in" in haystack
    if preferred == "tamilnadutourism":
        return "tamilnadutourism" in haystack or "tamil nadu tourism" in haystack
    if preferred.endswith(".nic.in"):
        return preferred in haystack
    return preferred in haystack

ANSWER_SECTION_TERMS = {
    "listed_places": {"tourist places", "palace", "temple", "museum", "kovil", "teppakulam"},
    "official_source": {"tourism", "tourist", "places", "temple", "museum", "district", "india", "tamil", "nadu", "kanyakumari", "kanniyakumari", "ooty", "kodaikanal"},
    "dress": {"dress", "attire", "dhoti", "saree", "salwar", "footwear", "men:", "women:"},
    "photography": {"photography", "camera", "mobile", "electronics", "locker", "cloakroom"},
    "timings": {"timings", "open", "closed", "hours", "daily", "best time"},
    "fees": {"entry fee", "entry fees", "ticket", "tickets", "camera fee", "cost", "darshan"},
    "emergency": {"emergency", "helpline", "hospital", "police", "ambulance"},
    "rules": {"rules", "customs", "guidelines", "permit", "safety"},
    "best_time": {"best time", "season", "visit", "weather", "months"},
    "how_to_reach": {"how to reach", "airport", "railway", "station", "road", "bus", "distance"},
    "history": {"history", "heritage", "built", "museum", "monument", "temple"},
    "culture": {"culture", "festival", "famous", "known", "food", "art"},
    "destination_guide": {"places", "attractions", "sightseeing", "tourist", "things to do", "visit", "guide"},
}

SECTION_STARTERS = {
    "dress code",
    "dress code:",
    "photography",
    "photography & electronics",
    "photography & electronics ban:",
    "timings",
    "timings:",
    "entry fees",
    "entry fees:",
    "emergency numbers",
    "emergency numbers:",
    "rules",
    "rules:",
    "highlights",
    "highlights:",
    "best time to visit",
    "best time to visit:",
}

def clean_rag_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^\[[^\]]+\]\s*", "", line)
    line = re.sub(r"^[-*]\s*", "", line)
    return line.strip()

def line_matches_intent(line: str, query_intent: Optional[str]) -> bool:
    if not query_intent:
        return True
    lower = line.lower()
    return any(term in lower for term in ANSWER_SECTION_TERMS.get(query_intent, set()))

def should_continue_intent_block(line: str, query_intent: Optional[str]) -> bool:
    if not query_intent:
        return False

    lower = clean_rag_line(line).lower()
    if not lower:
        return False

    if query_intent == "dress":
        return lower.startswith(("men:", "women:", "footwear:"))
    if query_intent == "photography":
        return lower.startswith(("lockers", "lockers & cloakroom", "commercial"))
    if query_intent == "emergency":
        return lower.startswith(("hospitals:", "tourist police", "police", "ambulance"))

    return False

def is_different_section(line: str, query_intent: Optional[str]) -> bool:
    if not query_intent:
        return False
    lower = clean_rag_line(line).lower()
    starter = lower.split(":", 1)[0].strip()
    if lower in SECTION_STARTERS or starter in SECTION_STARTERS:
        return not line_matches_intent(line, query_intent)
    return False

def extract_focused_lines(content: str, query_intent: Optional[str]) -> List[str]:
    raw_lines = [line for line in (content or "").splitlines() if clean_rag_line(line)]
    focused: List[str] = []
    collecting = False

    for raw_line in raw_lines:
        line = clean_rag_line(raw_line)
        if not line or line.startswith("["):
            continue

        if line_matches_intent(line, query_intent):
            focused.append(line)
            collecting = True
            continue

        if collecting and should_continue_intent_block(line, query_intent):
            focused.append(line)
            continue

        if collecting and is_different_section(line, query_intent):
            collecting = False

    deduped = []
    seen = set()
    for line in focused:
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(line)
    return deduped

def format_focused_rag_answer(query: str, results: List[RAGSearchResult]) -> str:
    query_intent = detect_query_intent(query)
    if not results:
        return ""

    if query_intent == "listed_places":
        place_names = extract_listed_place_names(results)
        if place_names:
            return "**Tourist Places Listed By Madurai District**\n\n" + "\n".join(
                f"- {name}" for name in place_names
            )

    if query_intent == "official_source":
        return format_official_source_answer(query, results)

    blocks = []
    for res in results:
        lines = extract_focused_lines(res.content, query_intent)
        if not lines:
            lines = [clean_rag_line(line) for line in res.content.splitlines() if clean_rag_line(line)][:4]

        if not lines:
            continue

        heading = f"**{res.destination}**"
        if query_intent == "fees":
            heading = f"**Entry Fee - {res.destination}**"
        elif query_intent == "timings":
            heading = f"**Timings - {res.destination}**"
        elif query_intent == "dress":
            heading = f"**Dress Code - {res.destination}**"
        elif query_intent == "photography":
            heading = f"**Photography Policy - {res.destination}**"

        blocks.append(f"{heading}\n\n" + "\n".join(lines))

    return "\n\n".join(blocks)

def format_official_source_answer(query: str, results: List[RAGSearchResult]) -> str:
    if "kanyakumari" in query.lower() or "kanniyakumari" in query.lower():
        spots = extract_kanniyakumari_spots(results)
        if spots:
            return "**Kanyakumari Tourist Spots**\n\n" + "\n".join(f"- {spot}" for spot in spots)

    query_words = query_terms(query)
    lines: List[str] = []
    seen = set()

    for res in results:
        content_lines = [
            clean_rag_line(line)
            for line in re.split(r"[\n\r]+", res.content)
            if clean_rag_line(line)
        ]

        for line in content_lines:
            lower = line.lower()
            if is_noisy_official_line(line):
                continue
            if len(line) < 55:
                continue

            line_terms = query_terms(line)
            if query_words and not (query_words & line_terms):
                continue

            key = lower[:180]
            if key in seen:
                continue
            seen.add(key)
            lines.append(line)
            if len(lines) >= 3:
                break

        if len(lines) >= 3:
            break

    if not lines:
        for res in results[:2]:
            for line in res.content.splitlines():
                line = clean_rag_line(line)
                if len(line) >= 55 and not is_noisy_official_line(line):
                    lines.append(line)
                if len(lines) >= 3:
                    break

    # For broad destination questions the useful overview is the answer. The
    # individual document name belongs in citations, not in the main heading.
    requested_city = infer_city_from_query(query, results[0].city or "Tourism")
    return f"**About {requested_city}**\n\n" + "\n\n".join(lines[:3])

def is_noisy_official_line(line: str) -> bool:
    lower = line.lower().strip()
    if lower.startswith("[") or "share on facebook" in lower or "formaly twitter" in lower:
        return True
    if lower.startswith(("80 places", "best.", "embark on a journey", "exploring delhi", "davas.")):
        return True
    if "clear all show results" in lower or "please apply filter" in lower:
        return True
    if re.fullmatch(r"(?:\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*°c\s*)+", lower):
        return True
    if re.fullmatch(r"[a-z\s&]+(?:clear all show results)?", lower) and len(lower.split()) > 8:
        return True
    if lower in {"delhi", "indian capital", "that beckon every traveller", "for every bucket list", "worth a thousand stories"}:
        return True
    return False

def extract_kanniyakumari_spots(results: List[RAGSearchResult]) -> List[str]:
    combined = " ".join(res.content for res in results).lower()
    known_spots = [
        ("Kanyakumari Beach", ["iconic scenic spot located on kanyakumari beach"]),
        ("Thiruvalluvar Statue", ["iconic stone statue of tamil poet thiruvalluvar"]),
        ("Kanyakumari Glass Bridge", ["connects two iconic landmarks", "vivekananda rock memorial and the thiruvalluvar statue"]),
        ("Vivekananda Rock Memorial", ["serene rock island dedicated to swami vivekananda"]),
        ("Kumari Amman Temple", ["kumari amman temple"]),
        ("Gandhi Memorial Mandapam", ["mahatma gandhi's ashes"]),
        ("Kamarajar Memorial", ["tribute to k. kamarajar"]),
        ("Sanguthurai Beach", ["picturesque coastal gem about 12 km east of kanyakumari"]),
        ("Vattakottai Fort", ["vattakottai fort"]),
        ("Suchindram Thanumalayan Temple", ["sri thanumalaya", "suchindrum"]),
        ("Nagaraja Temple", ["nagaraja temple"]),
        ("Thirparappu Falls", ["thirparappu falls"]),
        ("Pechiparai Dam", ["pechiparai dam"]),
        ("Mathoor Aqueduct", ["mathoor aqueduct"]),
        ("Kalikesam", ["kalikesam"]),
        ("Ulakkai Aruvi Falls", ["double-stream waterfall", "veerapuli reserve forest"]),
    ]

    spots = []
    for name, markers in known_spots:
        if any(marker in combined for marker in markers):
            spots.append(name)
    return spots

def extract_listed_place_names(results: List[RAGSearchResult]) -> List[str]:
    patterns = [
        r"\b(Thirumalai Nayak Palace)\b",
        r"\b(Thirupparankundram Temple)\b",
        r"\b(Sri Meenakshi\s+[–-]\s+Sundareswarar Temple)\b",
        r"\b(Sri Meenakshi\s+Sundareswarar Temple)\b",
        r"\b(Gandhi Museum(?: Madurai)?)\b",
        r"\b(Azhagar Kovil)\b",
        r"\b(?:Mariamman\s+)?(Teppakulam)\b",
    ]
    names: List[str] = []
    seen = set()
    combined = " ".join(res.content for res in results)

    for pattern in patterns:
        for match in re.finditer(pattern, combined, flags=re.IGNORECASE):
            name = re.sub(r"\s+", " ", match.group(1)).strip()
            normalized = name.lower().replace("madurai", "").strip()
            display = {
                "gandhi museum": "Gandhi Museum Madurai",
                "teppakulam": "Mariamman Teppakulam",
                "sri meenakshi sundareswarar temple": "Sri Meenakshi - Sundareswarar Temple",
            }.get(normalized, name)
            key = display.lower()
            if key not in seen:
                seen.add(key)
                names.append(display)

    return names

class RAGKnowledgeService:
    """
    Unified Shared RAG Knowledge Service for TouristAI multi-agent platform.
    Queries domain vector collections, applies source trust scoring, and generates structured citations.
    """

    def __init__(self):
        self.router = KnowledgeRouter()

    def query_rag(
        self,
        query: str,
        agent_name: str = "GeneralAgent",
        city: str = "Madurai",
        top_k: int = 4
    ) -> Dict[str, Any]:
        """
        Query trusted tourism knowledge base with routing, filtering, and source citations.
        """
        city = infer_city_from_query(query, city or "Madurai")
        if not is_city_covered(city):
            fallback_info = build_official_fallback(query, city)
            return {
                "has_knowledge": False,
                "query": query,
                "city": city,
                "agent": agent_name,
                "collections_searched": [],
                "context_text": "",
                "answer_text": "",
                "rag_intent": detect_query_intent(query),
                "citations": [],
                "raw_results": [],
                "coverage_status": "not_indexed",
                "coverage_message": f"No verified RAG knowledge is indexed for {city}.",
                "official_fallback": fallback_info,
                "answer_text": fallback_info["answer"],
            }

        agent_context = {"agent": agent_name, "city": city}
        route_plan = self.router.route_query(query, agent_context)
        terms = query_terms(query)
        query_intent = detect_query_intent(query)
        effective_top_k = 1 if query_intent in {"dress", "photography", "timings", "fees", "emergency"} else top_k

        db = get_db()
        results: List[RAGSearchResult] = []
        seen_chunk_ids = set()

        if db is not None:
            try:
                # Execute similarity search against loaded vector index
                docs_and_scores = db.similarity_search_with_score(query, k=top_k * 8)
                clean_city_lower = (city or "").strip().lower()

                for doc, raw_score in docs_and_scores:
                    meta = doc.metadata or {}
                    page_content = doc.page_content or ""
                    chunk_city = str(meta.get("city") or meta.get("destination") or "").strip().lower()

                    if not is_verified_knowledge_chunk(meta, page_content):
                        continue

                    if not matches_query_intent(query_intent, page_content, meta):
                        continue

                    if source_preference(query) and not matches_source_preference(query, meta):
                        continue

                    chunk_id = meta.get("chunk_id", "doc_chunk")
                    if chunk_id in seen_chunk_ids:
                        continue

                    content_terms = query_terms(page_content)
                    if terms and not (terms & content_terms):
                        continue

                    # Strict City Check: Ensure retrieved chunk actually pertains to requested city
                    if clean_city_lower and clean_city_lower not in {"none", "any"}:
                        if clean_city_lower not in page_content.lower() and clean_city_lower != chunk_city:
                            continue

                    trust_score = meta.get("trust_score", 100)
                    
                    # Compute weighted relevance score = similarity_score * (trust_score / 100)
                    norm_sim = max(0.0, 1.0 - (raw_score / 10.0))
                    weighted_score = norm_sim * (trust_score / 100.0)

                    results.append(
                        RAGSearchResult(
                            chunk_id=chunk_id,
                            content=page_content,
                            destination=meta.get("destination", city),
                            city=meta.get("city", city),
                            category=meta.get("category", "Tourism"),
                            source_url=meta.get("source_url"),
                            source_domain=meta.get("source_domain"),
                            trust_score=trust_score,
                            relevance_score=round(weighted_score, 3),
                            metadata=meta
                        )
                    )
                    seen_chunk_ids.add(chunk_id)
                    if len(results) >= effective_top_k:
                        break
            except Exception as e:
                print(f"[WARNING] RAG vector query exception: {e}")

        if query_intent in {"listed_places", "official_source"} and db is not None:
            try:
                clean_city_lower = (city or "").strip().lower()
                district_count = 0
                for doc in getattr(db.docstore, "_dict", {}).values():
                    meta = doc.metadata or {}
                    page_content = doc.page_content or ""
                    source_url = str(meta.get("source_url") or "").lower()
                    chunk_city = str(meta.get("city") or meta.get("destination") or "").strip().lower()

                    if query_intent == "listed_places" and "tourist-places" not in source_url and "madurai.nic.in" not in source_url:
                        continue

                    if query_intent == "official_source" and not matches_source_preference(query, meta):
                        continue

                    if not is_verified_knowledge_chunk(meta, page_content):
                        continue

                    if clean_city_lower and clean_city_lower not in {"none", "any"}:
                        if clean_city_lower not in page_content.lower() and clean_city_lower != chunk_city:
                            continue

                    chunk_id = meta.get("chunk_id", "doc_chunk")
                    if chunk_id in seen_chunk_ids:
                        continue

                    trust_score = meta.get("trust_score", 100)
                    results.append(
                        RAGSearchResult(
                            chunk_id=chunk_id,
                            content=page_content,
                            destination=meta.get("destination", city),
                            city=meta.get("city", city),
                            category=meta.get("category", "Tourism"),
                            source_url=meta.get("source_url"),
                            source_domain=meta.get("source_domain"),
                            trust_score=trust_score,
                            relevance_score=1.0,
                            metadata=meta
                        )
                    )
                    seen_chunk_ids.add(chunk_id)
                    district_count += 1
                    if district_count >= max(top_k, 6):
                        break
            except Exception as e:
                print(f"[WARNING] RAG district listing fallback exception: {e}")

        # If the FAISS store is stale/polluted, still protect key official seeded
        # knowledge by falling back to the curated source documents.
        if not results:
            try:
                from .seed_rag_knowledge import OFFICIAL_TOURISM_DOCUMENTS

                clean_city_lower = (city or "").strip().lower()
                scored_docs = []
                for doc in OFFICIAL_TOURISM_DOCUMENTS:
                    meta = doc.metadata or {}
                    page_content = doc.page_content or ""
                    chunk_city = str(meta.get("city") or "").strip().lower()
                    if clean_city_lower and clean_city_lower not in {"none", "any"} and clean_city_lower != chunk_city:
                        continue

                    if not matches_query_intent(query_intent, page_content, meta):
                        continue

                    content_terms = query_terms(page_content)
                    score = len(terms & content_terms)
                    if score:
                        scored_docs.append((score, doc))

                for _, doc in sorted(scored_docs, key=lambda item: item[0], reverse=True)[:effective_top_k]:
                    meta = doc.metadata or {}
                    chunk_id = meta.get("chunk_id", "curated_doc_chunk")
                    if chunk_id in seen_chunk_ids:
                        continue
                    results.append(
                        RAGSearchResult(
                            chunk_id=chunk_id,
                            content=doc.page_content,
                            destination=meta.get("destination", city),
                            city=meta.get("city", city),
                            category=meta.get("category", "Tourism"),
                            source_url=meta.get("source_url"),
                            source_domain=meta.get("source_domain"),
                            trust_score=meta.get("trust_score", 100),
                            relevance_score=1.0,
                            metadata=meta
                        )
                    )
                    seen_chunk_ids.add(chunk_id)
            except Exception as e:
                print(f"[WARNING] RAG curated fallback exception: {e}")

        if query_intent in {"listed_places", "official_source"}:
            district_results = [
                res for res in results
                if query_intent == "official_source" and matches_source_preference(query, res.metadata or {})
                or query_intent == "listed_places" and (
                    "madurai.nic.in" in str(res.source_url or "").lower()
                    or "tourist-places" in str(res.source_url or "").lower()
                )
            ]
            if district_results:
                results = district_results

        # Format synthesized output context & citations
        citations = []
        context_blocks = []

        for res in results:
            context_blocks.append(f"[{res.category} | {res.destination}]\n{res.content}")
            citations.append({
                "source_name": res.source_domain,
                "source_url": res.source_url,
                "trust_score": f"{res.trust_score}% (Verified)",
                "destination": res.destination
            })

        # Deduplicate citations
        unique_citations = {c["source_url"]: c for c in citations}.values()
        image_url = None
        image_urls = []
        if results:
            image_url = get_rag_image_url(results[0].destination, results[0].city)
            image_urls = get_rag_image_urls(results[0].destination, results[0].city)

        return {
            "has_knowledge": len(results) > 0,
            "query": query,
            "city": city,
            "agent": agent_name,
            "collections_searched": [c.value for c in route_plan.collections],
            "context_text": "\n\n".join(context_blocks),
            "answer_text": format_focused_rag_answer(query, results),
            "rag_intent": query_intent,
            "image_url": image_url,
            "image_urls": image_urls,
            "citations": list(unique_citations),
            "raw_results": [r.dict() for r in results]
        }

# Global singleton instance
rag_service = RAGKnowledgeService()
