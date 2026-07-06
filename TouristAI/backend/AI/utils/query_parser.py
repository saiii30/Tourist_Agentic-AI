"""
Free-text query parser + fuzzy destination resolver.

No LLM, no external API — just difflib + a normalized name cache.

Usage:
    from utils.query_parser import resolve_destination, extract_intent

    dest = resolve_destination("plan a trip to ooty from chennai")
    # -> {"id": 42, "name": "Ooty (Udhagamandalam)", "match": "ooty", "score": 0.91}

    intent = extract_intent("explore near coorg for 2 days")
    # -> {"intent": "explore", "days": 2}
"""

import re
import difflib
import threading
from database.postgres import get_connection

_CACHE = None
_LOCK = threading.Lock()

STOPWORDS = {
    "plan", "trip", "planning", "explore", "exploring", "visit", "visiting",
    "places", "place", "near", "around", "attractions", "attraction",
    "tourist", "spots", "spot", "for", "in", "to", "from", "and", "a",
    "the", "please", "give", "show", "me", "can", "you", "days", "day",
    "weekend", "holiday", "vacation", "tour", "guide", "best", "top",
    "food", "hotels", "hotel", "restaurants", "restaurant", "weather",
    "how", "what", "where", "when", "with", "family", "solo", "couple",
    "budget", "cheap", "luxury",
}


def _normalize(s: str) -> str:
    # strip anything in brackets: "Ooty (Udhagamandalam)" -> "Ooty"
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-zA-Z0-9 ]+", " ", s).lower()
    return re.sub(r"\s+", " ", s).strip()


def _load_cache():
    """Load all destinations once. Each entry stores every alias form."""
    global _CACHE
    with _LOCK:
        if _CACHE is not None:
            return _CACHE
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, destination_name FROM destinations")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        cache = []
        for did, name in rows:
            aliases = set()
            aliases.add(_normalize(name))                # "ooty"
            # add any bracketed alt name too: "Ooty (Udhagamandalam)" -> also "udhagamandalam"
            for m in re.findall(r"\(([^)]+)\)", name):
                aliases.add(_normalize(m))
            # split multi-word: also keep the last token as alias ("New Delhi" -> "delhi")
            tokens = _normalize(name).split()
            if len(tokens) > 1:
                aliases.add(tokens[-1])
            cache.append({"id": did, "name": name, "aliases": [a for a in aliases if a]})
        _CACHE = cache
        return _CACHE


def resolve_destination(query: str, min_score: float = 0.72):
    """
    Return the best-matching destination row for a free-text query, or None.
    Handles typos, partial names, alt names, extra words.
    """
    if not query:
        return None
    q_norm = _normalize(query)
    q_tokens = [t for t in q_norm.split() if t not in STOPWORDS and len(t) > 2]
    if not q_tokens:
        q_tokens = q_norm.split()

    cache = _load_cache()

    best = None
    best_score = 0.0
    best_alias = ""

    for entry in cache:
        for alias in entry["aliases"]:
            # 1) direct substring hit is strongest
            if alias in q_norm:
                score = 0.95 + min(0.05, len(alias) / 100)
            else:
                # 2) fuzzy against each meaningful token, take the max
                score = 0.0
                for tok in q_tokens:
                    s = difflib.SequenceMatcher(None, alias, tok).ratio()
                    if s > score:
                        score = s
                # 3) also fuzzy against the whole query (helps multi-word aliases)
                s_full = difflib.SequenceMatcher(None, alias, q_norm).ratio()
                if s_full > score:
                    score = s_full
            if score > best_score:
                best_score = score
                best = entry
                best_alias = alias

    if best and best_score >= min_score:
        return {
            "id":    best["id"],
            "name":  best["name"],
            "match": best_alias,
            "score": round(best_score, 3),
        }
    return None


# ---------- intent + duration ----------

_INTENT_PATTERNS = [
    ("plan",    r"\b(plan|planning|itinerary|schedule)\b"),
    ("explore", r"\b(explore|exploring|discover|near|around|places|attractions|things to do)\b"),
    ("food",    r"\b(food|restaurant|eat|cuisine|dish)\b"),
    ("hotel",   r"\b(hotel|stay|accommodation|resort|lodge)\b"),
    ("weather", r"\b(weather|climate|temperature|rain)\b"),
]


def extract_intent(query: str) -> dict:
    q = (query or "").lower()
    intent = "explore"
    for name, pat in _INTENT_PATTERNS:
        if re.search(pat, q):
            intent = name
            break
    days = None
    m = re.search(r"(\d+)\s*(?:day|days|night|nights)\b", q)
    if m:
        days = int(m.group(1))
    return {"intent": intent, "days": days}
