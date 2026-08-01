"""
Discover Places Agent
---------------------
Given a user query like "places to explore in Chennai" or "places near Goa",
returns a ChatGPT-style categorized list of top places using Google Places
Text Search, enriched with Wikipedia thumbnails + article URLs.

No Unsplash / stock fallback. image=None when Wikipedia has nothing.
"""

import os
import re
import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

# ---------------------------------------------------------------------------
# Categories to search for. Add/remove freely.
# ---------------------------------------------------------------------------
CATEGORIES = [
    {"key": "beaches",   "label": "Beaches",                  "query": "famous beaches",                                    "icon": "🏖️", "terms": ["beach", "coast", "shore", "seaside", "ocean", "sea walk"]},
    {"key": "temples",   "label": "Temples",                  "query": "famous temples",                                    "icon": "🛕", "terms": ["temple", "mandir", "mosque", "church", "cathedral", "gurudwara", "shrine"]},
    {"key": "heritage",  "label": "Historical & Cultural",    "query": "historical monuments and heritage sites",           "icon": "🏛️", "terms": ["fort", "palace", "mahal", "monument", "heritage", "historic", "museum", "tomb", "memorial", "gate", "ruins"]},
    {"key": "nature",    "label": "Nature & Wildlife",        "query": "national parks wildlife sanctuaries and gardens",   "icon": "🌳", "terms": ["park", "wildlife", "sanctuary", "zoo", "garden", "forest", "lake", "waterfall"]},
    {"key": "mountains", "label": "Mountains & Viewpoints",   "query": "mountains hills and viewpoints",                    "icon": "⛰️", "terms": ["mountain", "hill", "viewpoint", "view point", "peak", "trek", "valley"]},
    {"key": "shopping",  "label": "Shopping",                 "query": "popular shopping streets and malls",                "icon": "🛍️", "terms": ["mall", "market", "bazaar", "shopping", "emporium"]},
    {"key": "cuisine",   "label": "Food & Cuisine",           "query": "famous local food restaurants",                     "icon": "🍽️", "terms": ["restaurant", "cafe", "café", "eatery", "food", "dining", "dhaba", "bakery"]},
    {"key": "museums",   "label": "Museums & Art",            "query": "top museums and art galleries",                     "icon": "🖼️", "terms": ["museum", "gallery", "art", "exhibition"]},
]

TOP_N_PER_CATEGORY = 5

INTEREST_CATEGORY_MAP = {
    "nature": {"nature", "mountains", "beaches"},
    "wildlife": {"nature"},
    "adventure": {"mountains", "nature", "beaches"},
    "history": {"heritage", "museums", "temples"},
    "heritage": {"heritage", "museums", "temples"},
    "culture": {"heritage", "temples", "museums"},
    "cultural": {"heritage", "temples", "museums"},
    "food": {"cuisine"},
    "cuisine": {"cuisine"},
    "restaurant": {"cuisine"},
    "shopping": {"shopping"},
    "kids": {"nature", "museums", "beaches"},
    "family": {"nature", "museums", "beaches", "temples"},
    "photography": {"beaches", "mountains", "heritage", "nature"},
    "temple": {"temples"},
    "spiritual": {"temples"},
    "art": {"museums", "heritage"},
}


def _preferred_category_keys(user_query: str) -> set[str]:
    q = (user_query or "").lower()
    preferred = set()
    for term, category_keys in INTEREST_CATEGORY_MAP.items():
        if term in q:
            preferred.update(category_keys)
    return preferred

# ---------------------------------------------------------------------------
# Location extraction
# ---------------------------------------------------------------------------
_LOCATION_PATTERNS = [
    r"places?\s+to\s+explore\s+in\s+(.+)",
    r"places?\s+to\s+visit\s+in\s+(.+)",
    r"things?\s+to\s+do\s+in\s+(.+)",
    r"what\s+to\s+see\s+in\s+(.+)",
    r"places?\s+(?:near|nera)\s+(.+)",
    r"places?\s+in\s+(.+)",
    r"explore\s+(.+)",
    r"visit\s+(.+)",
    r"tourist\s+places?\s+in\s+(.+)",
    r"attractions?\s+in\s+(.+)",
    r"trip\s+to\s+(.+)",
]

def extract_location(user_query: str) -> str:
    q = (user_query or "").strip().lower()
    for pat in _LOCATION_PATTERNS:
        m = re.search(pat, q)
        if m:
            loc = m.group(1).strip(" ?.!,\"'")
            if loc:
                return loc.title()
    # fallback: return the whole thing cleaned
    return (user_query or "").strip(" ?.!,\"'").title()


# ---------------------------------------------------------------------------
# Google Places Text Search (v1)
# ---------------------------------------------------------------------------
def _google_text_search(text_query: str, api_key: str, max_results: int = TOP_N_PER_CATEGORY):
    try:
        r = requests.post(
            "https://places.googleapis.com/v1/places:searchText",
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": (
                    "places.id,"
                    "places.displayName,"
                    "places.formattedAddress,"
                    "places.rating,"
                    "places.userRatingCount,"
                    "places.location,"
                    "places.editorialSummary,"
                    "places.primaryType,"
                    "places.types,"
                    "places.googleMapsUri,"
                    "places.websiteUri,"
                    "places.photos,"
                    "places.nationalPhoneNumber,"
                    "places.internationalPhoneNumber,"
                    "places.regularOpeningHours,"
                    "places.currentOpeningHours,"
                    "places.accessibilityOptions,"
                    "places.parkingOptions,"
                    "places.paymentOptions,"
                    "places.priceLevel,"
                    "places.businessStatus"
                ),
            },
            json={"textQuery": text_query, "maxResultCount": max_results},
            timeout=20,
        )
        if not r.ok:
            print(f"[discover] Google Places API returned {r.status_code}. No fallback places source configured.")
            return []
        return r.json().get("places", []) or []
    except Exception as e:
        print(f"[discover] Google Places exception: {e}")
        return []


def _google_place_details(place_id: str, api_key: str) -> dict:
    """Get a place's photo and rich visitor details when text search omits them."""
    if not place_id:
        return {}
    try:
        response = requests.get(
            f"https://places.googleapis.com/v1/places/{place_id}",
            headers={
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": (
                    "location,photos,nationalPhoneNumber,internationalPhoneNumber,"
                    "regularOpeningHours,currentOpeningHours,accessibilityOptions,"
                    "parkingOptions,paymentOptions,priceLevel,businessStatus"
                ),
            },
            timeout=15,
        )
        return response.json() if response.ok else {}
    except (requests.RequestException, ValueError):
        return {}


# ---------------------------------------------------------------------------
# Wikipedia enrichment (thumbnail + article URL)
# ---------------------------------------------------------------------------
WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_REST = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_HEADERS = {"User-Agent": "TouristAI/1.0 (contact@example.com)"}
BAD_WIKI_TYPES = {"disambiguation"}
BAD_WIKI_DESCRIPTIONS = ("actor", "actress", "singer", "politician", "film", "movie", "song", "album", "band", "author", "writer", "player")
PLACE_HINTS = ("town", "city", "village", "beach", "waterfall", "temple", "fort", "hill", "mountain", "island", "district", "state", "region", "national park", "sanctuary", "monument", "lake", "river", "valley", "cave", "ghat", "palace", "museum", "market", "square", "park", "garden")
_STOPWORDS = {
    "the","of","and","in","at","on",
    "shri","sri","shree","श्री",
    "temple","beach","park","fort",
    "palace","museum","garden","lake",
    "hill","hills","mountain","market",
    "mall","church","cathedral","mosque",
    "gurudwara","monument","memorial",
    "point","view","viewpoint","national",
    "sanctuary","wildlife","zoo"
}

def _significant_tokens(text: str) -> set[str]:
    toks = re.findall(
        r"[a-zA-Z\u00C0-\uFFFF]+",
        (text or "").lower()
    )

    return {
        t
        for t in toks
        if len(t) >= 4 and t not in _STOPWORDS
    }


# def _wiki_page(query: str) -> dict | None:
#     """Use the first genuine place page from Wikipedia's ranked results."""
#     try:
#         search_response = requests.get(
#             WIKI_API,
#             params={"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": 5},
#             headers=WIKI_HEADERS,
#             timeout=8,
#         )
#         if not search_response.ok:
#             return None
#         hits = search_response.json().get("query", {}).get("search", [])
#         for hit in hits:
#             summary_response = requests.get(WIKI_REST + quote(hit["title"]), headers=WIKI_HEADERS, timeout=8)
#             if not summary_response.ok:
#                 continue
#             data = summary_response.json()
#             description = (data.get("description") or "").lower()
#             extract = (data.get("extract") or "").lower()
#             if data.get("type") in BAD_WIKI_TYPES or any(word in description for word in BAD_WIKI_DESCRIPTIONS):
#                 continue
#             if any(hint in description for hint in PLACE_HINTS) or any(hint in extract[:400] for hint in PLACE_HINTS) or data.get("coordinates"):
#                 return data
#     except (requests.RequestException, ValueError, KeyError) as e:
#         print(f"[discover] Wikipedia lookup failed for '{query}': {e}")
#     return None
def _wiki_page(query: str, place_name: str = "") -> dict | None:
    """Return a Wikipedia summary ONLY if its title actually matches the place."""
    try:
        search_response = requests.get(
            WIKI_API,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 8,
            },
            headers=WIKI_HEADERS,
            timeout=8,
        )

        if not search_response.ok:
            return None

        hits = search_response.json().get("query", {}).get("search", [])

        want = _significant_tokens(place_name or query)

        for hit in hits:
            title = hit.get("title", "")
            title_toks = _significant_tokens(title)

            # Require title overlap
            if want and not (want & title_toks):
                continue

            summary_response = requests.get(
                WIKI_REST + quote(title),
                headers=WIKI_HEADERS,
                timeout=8,
            )

            if not summary_response.ok:
                continue

            data = summary_response.json()

            description = (
                data.get("description") or ""
            ).lower()

            extract = (
                data.get("extract") or ""
            ).lower()

            if (
                data.get("type") in BAD_WIKI_TYPES
                or any(
                    w in description
                    for w in BAD_WIKI_DESCRIPTIONS
                )
            ):
                continue

            if (
                any(h in description for h in PLACE_HINTS)
                or any(h in extract[:400] for h in PLACE_HINTS)
                or data.get("coordinates")
            ):
                if not want or (want & title_toks):
                    return data

    except (
        requests.RequestException,
        ValueError,
        KeyError,
    ) as e:
        print(
            f"[discover] Wikipedia lookup failed for '{query}': {e}"
        )

    return None

# @lru_cache(maxsize=512)
# def _wiki_info(title: str, location_hint: str) -> dict:
#     """Resolve the same strict Wikipedia/Wikimedia image strategy as ResponseBuilder."""
#     for query in (f"{title}, {location_hint}", f"{title} {location_hint}", title):
#         # data = _wiki_page(query)
#         data = _wiki_page(
#     query,
#     place_name=title
# )
#         if not data:
#             continue
#         image = (data.get("originalimage") or {}).get("source") or (data.get("thumbnail") or {}).get("source")
#         page_url = ((data.get("content_urls") or {}).get("desktop") or {}).get("page")
#         if image and page_url:
  
#             return {"image": image, "url": page_url, "searchFallback": False}
#     return {"image": None, "url": None, "searchFallback": False}

@lru_cache(maxsize=512)
def _wiki_info(title: str, location_hint: str) -> dict:
    """Resolve the same strict Wikipedia/Wikimedia image strategy as ResponseBuilder."""

    for query in (
        f"{title}, {location_hint}",
        f"{title} {location_hint}",
        title,
    ):
        data = _wiki_page(query, place_name=title)

        if not data:
            continue

        image = (
            (data.get("originalimage") or {}).get("source")
            or (data.get("thumbnail") or {}).get("source")
        )

        page_url = (
            ((data.get("content_urls") or {}).get("desktop") or {}).get("page")
        )

        # Accept article even if image is missing
        if page_url:
            return {
                "image": image,
                "url": page_url,
                "searchFallback": False,
            }

    # No matching article found
    search_url = (
        f"https://en.wikipedia.org/w/index.php?search="
        f"{quote(f'{title} {location_hint}')}"
    )

    return {
        "image": None,
        "url": search_url,
        "searchFallback": True,
    }
  


def _matches_category(place: dict, category: dict) -> bool:
    """Google text search can return general attractions; reject misclassified ones."""
    searchable = " ".join([
        ((place.get("displayName") or {}).get("text") or ""),
        place.get("formattedAddress") or "",
        ((place.get("editorialSummary") or {}).get("text") or ""),
        place.get("primaryType") or "",
        " ".join(place.get("types") or []),
    ]).lower()
    return any(term in searchable for term in category["terms"])


# ---------------------------------------------------------------------------
# Per-category worker
# ---------------------------------------------------------------------------
# def _build_category(cat: dict, location: str, api_key: str) -> dict:
#     text_query = f"{cat['query']} in {location}"
#     places = _google_text_search(text_query, api_key, TOP_N_PER_CATEGORY)
#     places = [place for place in places if _matches_category(place, cat)]

#     enriched = []
#     # Parallelize Wikipedia calls per category
#     # Wikipedia throttles bursts of parallel summary requests. Keep this small
#     # so every card gets a real response instead of an HTML/429 error page.
#     with ThreadPoolExecutor(max_workers=min(2, max(1, len(places)))) as ex:
#         futures = {}
#         for p in places:
#             name = ((p.get("displayName") or {}).get("text") or "").strip()
#             if not name:
#                 continue
#             futures[ex.submit(_wiki_info, name, location)] = p

#         for fut in as_completed(futures):
#             p = futures[fut]
#             name = ((p.get("displayName") or {}).get("text") or "").strip()
#             wiki = fut.result() or {"image": None, "url": None}
#             # Text Search frequently omits photos. Place Details provides the
#             # exact Google photo for the same place when Wikipedia has none.
#             details = _google_place_details(p.get("id", ""), api_key) if not wiki.get("image") and not p.get("photos") else {}
#             place = {**p, **details}
#             enriched.append({
#                 "id": place.get("id") or name,
#                 "name": name,
#                 "address": place.get("formattedAddress", "") or "",
#                 "rating": place.get("rating"),
#                 "ratingCount": place.get("userRatingCount"),
#                 "description": (place.get("editorialSummary") or {}).get("text", "") or "",
#                 "image": wiki.get("image"),
#                 # Google Places has a photo for many venues that do not have a
#                 # usable Wikipedia thumbnail. The API layer proxies this name
#                 # so the browser never receives the Google API key.
#                 "googlePhotoName": ((place.get("photos") or [{}])[0].get("name")),
#                 "wikiUrl": wiki.get("url"),
#                 "wikiSearchFallback": wiki.get("searchFallback", False),
#                 "mapsUrl": place.get("googleMapsUri"),
#                 "website": place.get("websiteUri"),
#                 "phone": place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber"),
#                 "hours": (place.get("currentOpeningHours") or {}).get("weekdayDescriptions") or (place.get("regularOpeningHours") or {}).get("weekdayDescriptions") or [],
#                 "accessibility": place.get("accessibilityOptions") or {},
#                 "parking": place.get("parkingOptions") or {},
#                 "payment": place.get("paymentOptions") or {},
#                 "priceLevel": place.get("priceLevel"),
#             })

#     # Preserve Google's ordering
#     order = {((p.get("displayName") or {}).get("text") or ""): i for i, p in enumerate(places)}
#     enriched.sort(key=lambda x: order.get(x["name"], 999))

#     return {
#         "key": cat["key"],
#         "label": cat["label"],
#         "icon": cat["icon"],
#         "places": enriched,
#     }
def _build_category(cat: dict, location: str, api_key: str) -> dict:
    text_query = f"{cat['query']} in {location}"
    places = _google_text_search(text_query, api_key, TOP_N_PER_CATEGORY)
    places = [place for place in places if _matches_category(place, cat)]

    enriched = []

    # Parallelize Wikipedia calls per category
    with ThreadPoolExecutor(max_workers=min(2, max(1, len(places)))) as ex:
        futures = {}

        for p in places:
            name = ((p.get("displayName") or {}).get("text") or "").strip()

            if not name:
                continue

            futures[ex.submit(_wiki_info, name, location)] = p

        for fut in as_completed(futures):
            p = futures[fut]

            name = (
                (p.get("displayName") or {}).get("text") or ""
            ).strip()

            wiki = fut.result() or {
                "image": None,
                "url": None,
                "searchFallback": False,
            }

            # ALWAYS fetch Place Details
            # Google photo should be the primary image source
            details = _google_place_details(
                p.get("id", ""),
                api_key,
            )

            place = {**p, **details}

            google_photo_name = (
                (place.get("photos") or [{}])[0].get("name")
            )

            loc = place.get("location", {})
            lat = loc.get("latitude")
            lng = loc.get("longitude")

            enriched.append({
                "id": place.get("id") or name,
                "name": name,
                "address": place.get("formattedAddress", "") or "",
                "rating": place.get("rating"),
                "ratingCount": place.get("userRatingCount"),
                "latitude": lat,
                "longitude": lng,

                "description": (
                    (place.get("editorialSummary") or {}).get("text", "")
                    or ""
                ),

                # Keep the exact Wikipedia result as a browser fallback if the
                # Google photo proxy cannot load this place's primary photo.
                "image": wiki.get("image"),

                # Frontend should use this first
                "googlePhotoName": google_photo_name,

                "wikiUrl": wiki.get("url"),
                "wikiSearchFallback": wiki.get(
                    "searchFallback",
                    False,
                ),

                "mapsUrl": place.get("googleMapsUri"),
                "website": place.get("websiteUri"),

                "phone": (
                    place.get("nationalPhoneNumber")
                    or place.get("internationalPhoneNumber")
                ),

                "hours": (
                    (place.get("currentOpeningHours") or {}).get(
                        "weekdayDescriptions"
                    )
                    or
                    (place.get("regularOpeningHours") or {}).get(
                        "weekdayDescriptions"
                    )
                    or []
                ),

                "accessibility": (
                    place.get("accessibilityOptions") or {}
                ),

                "parking": (
                    place.get("parkingOptions") or {}
                ),

                "payment": (
                    place.get("paymentOptions") or {}
                ),

                "priceLevel": place.get("priceLevel"),
            })

    # Preserve Google's ordering
    order = {
        ((p.get("displayName") or {}).get("text") or ""): i
        for i, p in enumerate(places)
    }

    enriched.sort(
        key=lambda x: order.get(
            x["name"],
            999,
        )
    )

    return {
        "key": cat["key"],
        "label": cat["label"],
        "icon": cat["icon"],
        "places": enriched,
    }

# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------
def discover_places(user_query: str) -> dict:
    """
    Returns:
      {
        "location": "Chennai",
        "categories": [
          {"key": "beaches", "label": "Beaches", "icon": "🏖️", "places": [...]},
          ...
        ],
        "followUp": "How many days are you planning to spend in Chennai?..."
      }
    """
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        return {
            "location": extract_location(user_query),
            "categories": [],
            "error": "GOOGLE_PLACES_API_KEY not configured on the server.",
        }

    location = extract_location(user_query)
    preferred_keys = _preferred_category_keys(user_query)

    categories_out = []
    # Run categories in parallel too
    # Each category performs Wikipedia lookups; two category workers keeps the
    # total Wikimedia concurrency within its public API limits.
    with ThreadPoolExecutor(max_workers=min(2, len(CATEGORIES))) as ex:
        futures = {ex.submit(_build_category, cat, location, api_key): cat for cat in CATEGORIES}
        results = {}
        for fut in as_completed(futures):
            cat = futures[fut]
            try:
                results[cat["key"]] = fut.result()
            except Exception as e:
                print(f"[discover] category {cat['key']} failed: {e}")

    # Keep the original CATEGORIES order and drop empty ones
    for cat in CATEGORIES:
        block = results.get(cat["key"])
        if block and block.get("places"):
            categories_out.append(block)

    if preferred_keys:
        categories_out.sort(
            key=lambda block: (
                0 if block.get("key") in preferred_keys else 1,
                next((idx for idx, cat in enumerate(CATEGORIES) if cat["key"] == block.get("key")), 999),
            )
        )
        print(f"[LOG][DISCOVERY_CATEGORIES] interests={sorted(preferred_keys)}, ordered={[c.get('key') for c in categories_out]}")

    return {
        "location": location,
        "categories": categories_out,
        "followUp": (
            f"How many days are you planning to spend in {location}? "
            "I can put together the best itinerary for you."
        ),
    }


# def is_discover_query(user_query: str) -> bool:
#     """Heuristic to detect 'places near/in/to explore' style questions."""
#     if not user_query:
#         return False
#     q = user_query.lower()
#     triggers = [
#         "places to explore", "places to visit", "things to do",
#         "what to see", "places near", "places in",
#         "tourist places", "attractions in", "explore ",
#     ]
#     return any(t in q for t in triggers)




def is_discover_query(user_query: str) -> bool:
    """Heuristic to detect 'places near/in/to explore' style questions."""
    if not user_query:
        return False
    # Collapse whitespace so "places  near chennai" still matches.
    q = re.sub(r"\s+", " ", user_query.lower()).strip()
    triggers = [
        "places to explore", "places to visit", "things to do",
        "what to see", "places near", "places in", "place in", "place near",
        "tourist places", "attractions in", "attractions near",
        "explore ", "visit ", "trip to", "travel to", "sightseeing",
        "top places", "best places", "must visit", "must see",
    ]
    return any(t in q for t in triggers)
