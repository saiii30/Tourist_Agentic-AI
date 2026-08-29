# backend/AI/chat_flow.py
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


KNOWN_DESTINATIONS = {
    "madurai": "Madurai",
    "meenakshi": "Madurai",
    "thirumalai": "Madurai",
    "kanyakumari": "Kanniyakumari",
    "kanniyakumari": "Kanniyakumari",
    "ooty": "Ooty",
    "nilgiris": "Ooty",
    "kodaikanal": "Kodaikanal",
    "chennai": "Chennai",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "uttar pradesh": "Uttar Pradesh",
    "rajasthan": "Rajasthan",
    "tamil nadu": "Tamil Nadu",
    "tamilnadu": "Tamil Nadu",
    "goa": "Goa",
    "kerala": "Kerala",
    "karnataka": "Karnataka",
    "maharashtra": "Maharashtra",
    "gujarat": "Gujarat",
    "uttarakhand": "Uttarakhand",
    "himachal pradesh": "Himachal Pradesh",
    "west bengal": "West Bengal",
    "punjab": "Punjab",
    "odisha": "Odisha",
    "assam": "Assam",
    "sikkim": "Sikkim",
    "dindigul": "Dindigul",
    "theni": "Theni",
    "trichy": "Trichy",
    "tiruchirappalli": "Trichy",
    "salem": "Salem",
    "jaipur": "Jaipur",
    "udaipur": "Udaipur",
    "paris": "Paris",
    "kyoto": "Kyoto",
    "bengaluru": "Bengaluru",
    "japan": "Japan",
}

INTENT_KEYWORDS = {
    "recommendation": {"recommend", "suggest", "best place", "where should", "where can"},
    "attraction": {"things to do", "places to visit", "attractions", "sightseeing", "what to see", "must see"},
    "hotel": {"hotel", "stay", "resort", "room", "accommodation", "lodge"},
    "restaurant": {"restaurant", "food", "eat", "cafe", "dinner", "lunch", "breakfast", "veg", "non veg"},
    "weather": {"weather", "forecast", "temperature", "rain", "climate"},
    "transport": {"flight", "train", "bus", "cab", "taxi", "transport", "ticket", "travel options"},
    "itinerary": {"plan", "trip", "itinerary", "vacation", "holiday", "tour"},
}

RAG_KNOWLEDGE_PHRASES = {
    "about this place",
    "attractions",
    "best season",
    "best time",
    "culture",
    "dress code",
    "festival",
    "famous for",
    "guide",
    "heritage",
    "history",
    "how to reach",
    "local tips",
    "nearby places",
    "places to visit",
    "photography",
    "camera",
    "mobile allowed",
    "entry fee",
    "ticket price",
    "timings",
    "opening hours",
    "closed days",
    "rules",
    "customs",
    "helpline",
    "emergency",
    "permit",
    "safety",
    "tourist places listed",
    "tourist places",
    "places listed",
    "listed by",
    "official website",
    "district website",
    "incredible india",
    "tamil nadu tourism",
    "archaeological survey",
    "asi monuments",
    "tourist spots",
    "tourist attractions",
    "things to do",
    "travel guide",
    "visit guide",
    "known for",
    "special about",
}

RAG_OPENERS = (
    "can you suggest",
    "give me",
    "how can i",
    "how do i",
    "what is",
    "what are",
    "what does",
    "where can",
    "tell about",
    "tell me about",
    "explain",
    "is there",
    "are there",
    "suggest",
)

TOURISM_CONTEXT_TERMS = {
    "attraction",
    "attractions",
    "beach",
    "fort",
    "heritage",
    "hill station",
    "lake",
    "monument",
    "museum",
    "palace",
    "park",
    "pilgrimage",
    "place",
    "places",
    "sightseeing",
    "temple",
    "tourism",
    "tourist",
    "travel",
    "viewpoint",
}


@dataclass
class ChatFlowPlan:
    intent: str
    confidence: float
    destination: Optional[str] = None
    entities: Dict[str, str] = field(default_factory=dict)
    should_use_direct_rag: bool = False
    should_start_trip: bool = False
    should_reset_questionnaire: bool = False
    reason: str = ""
    loader_stages: List[Dict[str, str]] = field(default_factory=list)


def normalize_query(question: str) -> str:
    return re.sub(r"\s+", " ", (question or "").strip().lower())


def infer_destination(question: str) -> Optional[str]:
    lower = normalize_query(question)
    # Prefer the canonical destination dictionary. Generic grammar such as
    # "best place to visit" must never turn the verb "visit" into a city.
    for key, destination in KNOWN_DESTINATIONS.items():
        if re.search(rf"\b{re.escape(key)}\b", lower):
            return destination
    patterns = [
        r"\b(?:trip|travel|itinerary|iternary|vacation|holiday|tour)\s+(?:to|in|for)\s+([A-Za-z][A-Za-z .'-]*?)(?=\s+from\b|\s+for\s+\d|,|\?|$)",
        r"\b\d+\s*[- ]?days?\s+([A-Za-z][A-Za-z .'-]*?)\s+trip\b",
        r"\b(?:in|about|for|to)\s+([A-Za-z][A-Za-z .'-]*?)(?=\s+(?:tomorrow|today|on|for|from|history|trip)\b|,|\?|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, question, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if candidate.lower() not in {"visit", "travel", "trip", "place", "places", "destination"}:
                return candidate.title()
    return None


def extract_basic_entities(question: str) -> Dict[str, str]:
    lower = normalize_query(question)
    entities: Dict[str, str] = {}
    destination = infer_destination(question)
    if destination:
        entities["destination"] = destination

    days_match = re.search(r"\b(\d{1,2})\s*[- ]?days?\b", lower)
    if days_match:
        entities["days"] = days_match.group(1)

    travelers_match = re.search(r"\b(\d{1,2})\s*(?:people|person|persons|traveller|travellers|traveler|travelers)\b", lower)
    if travelers_match:
        entities["travelers"] = travelers_match.group(1)

    source_match = re.search(r"\bfrom\s+([a-z][a-z .'-]*?)(?=\s+to\b|\s+starting\b|\s+on\b|,|$)", lower)
    if source_match:
        entities["current_location"] = source_match.group(1).strip().title()

    origin_duration_match = re.search(
        r"\bfrom\s+([a-z][a-z .'-]*?)(?=\s+for\s+(?:a\s+)?\d{1,2}\s*[- ]?days?\b)",
        lower,
    )
    if origin_duration_match:
        entities["current_location"] = origin_duration_match.group(1).strip().title()

    route_match = re.search(
        r"\bfrom\s+([a-z][a-z .'-]*?)\s+to\s+([a-z][a-z .'-]*?)(?=\s+(?:on|today|tomorrow|next)\b|,|\?|$)",
        lower,
    )
    if route_match:
        entities["current_location"] = route_match.group(1).strip().title()
        entities["destination"] = route_match.group(2).strip().title()

    for keyword, mode in (("train", "Train"), ("railway", "Train"), ("flight", "Flight"), ("plane", "Flight"), ("bus", "Bus"), ("cab", "Car"), ("taxi", "Car"), ("car", "Car")):
        if keyword_matches(lower, keyword):
            entities["travel_mode"] = mode
            break

    date_match = re.search(r"\b(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\b", question)
    if date_match:
        entities["travel_date"] = date_match.group(1)
    elif "tomorrow" in lower:
        entities["travel_date"] = "tomorrow"

    budget_match = re.search(r"(?:rs\.?|₹|inr)\s*([0-9,]+)", lower)
    if budget_match:
        entities["budget_amount"] = budget_match.group(1).replace(",", "")
    elif any(word in lower for word in ["low budget", "cheap", "budget friendly"]):
        entities["budget"] = "Low"
    elif "luxury" in lower:
        entities["budget"] = "Luxury"
    elif "moderate" in lower:
        entities["budget"] = "Moderate"

    for season in ("summer", "winter", "monsoon", "spring", "autumn"):
        if keyword_matches(lower, season):
            entities["season"] = season.title()
            break

    interest_terms = {
        "nature": "Nature", "history": "History", "heritage": "History",
        "adventure": "Adventure", "food": "Food", "photography": "Photography",
        "beach": "Beaches", "temple": "Temples", "hill station": "Hill stations",
    }
    interests = [label for term, label in interest_terms.items() if keyword_matches(lower, term)]
    if interests:
        entities["interests"] = ", ".join(dict.fromkeys(interests))

    return entities


def classify_intent(question: str) -> tuple[str, float, str]:
    lower = normalize_query(question)
    scores = {intent: 0 for intent in INTENT_KEYWORDS}
    for intent, keywords in INTENT_KEYWORDS.items():
        scores[intent] = sum(1 for keyword in keywords if keyword_matches(lower, keyword))

    recommendation_request = bool(re.search(
        r"\b(?:best|good|suitable|recommended?)\s+(?:tourist\s+)?(?:place|places|destination|destinations)\b|"
        r"\bwhere\s+(?:should|can)\s+(?:i|we)\s+(?:go|visit)|"
        r"\b(?:recommend|suggest)\s+(?:a\s+|some\s+)?(?:place|places|destination|destinations)",
        lower,
    ))
    if recommendation_request:
        return "recommendation", 0.96, "matched destination-recommendation request"

    attraction_request = any(phrase in lower for phrase in (
        "things to do", "places to visit", "tourist places", "tourist attractions",
        "attractions in", "attractions near", "sightseeing", "what to see",
        "must visit", "must see", "places to explore",
    ))
    if attraction_request and infer_destination(question):
        return "attraction", 0.96, "matched attraction-discovery request"

    # A specific operational request wins over a generic mention of "trip".
    for specific in ("weather", "transport", "hotel", "restaurant"):
        if scores[specific] > 0:
            return specific, min(0.95, 0.65 + scores[specific] * 0.12), f"matched {specific} keywords"

    explicit_planning = bool(re.search(r"\b(?:plan|make|create|build|generate|estimate)\b.*\b(?:trip|itinerary|iternary|vacation|holiday|tour)\b", lower))
    if explicit_planning or "iternary" in lower:
        return "itinerary", min(0.98, 0.7 + scores["itinerary"] * 0.08), "matched trip-planning keywords"

    if any(phrase in lower for phrase in RAG_KNOWLEDGE_PHRASES):
        return "knowledge", 0.9, "matched knowledge phrase"

    if lower.startswith(RAG_OPENERS) and infer_destination(question):
        return "knowledge", 0.75, "informational opener with destination"

    if "visa" in lower:
        return "knowledge", 0.85, "matched practical travel knowledge"

    if infer_destination(question) and any(keyword_matches(lower, term) for term in TOURISM_CONTEXT_TERMS):
        return "knowledge", 0.78, "tourism question with destination"

    best_intent, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score > 0:
        return best_intent, min(0.95, 0.55 + best_score * 0.15), f"matched {best_intent} keywords"

    return "general", 0.45, "fallback general chat"


def keyword_matches(lower_query: str, keyword: str) -> bool:
    if " " in keyword:
        return keyword in lower_query
    return bool(re.search(rf"\b{re.escape(keyword)}s?\b", lower_query))


def build_loader_stages(intent: str) -> List[Dict[str, str]]:
    base = [{"stage": "understanding", "message": "Understanding your request", "detail": "Reading intent and destination."}]
    if intent == "knowledge":
        return base + [
            {"stage": "knowledge", "message": "Checking trusted tourism knowledge", "detail": "Looking in verified RAG sources."},
            {"stage": "building", "message": "Preparing a focused answer", "detail": "Formatting the exact details and citations."},
        ]
    if intent == "recommendation":
        return base + [
            {"stage": "recommendations", "message": "Finding suitable destinations", "detail": "Matching season, duration, origin and interests."},
            {"stage": "building", "message": "Comparing the best options", "detail": "Preparing practical recommendations."},
        ]
    if intent == "attraction":
        return base + [
            {"stage": "attractions", "message": "Discovering places to visit", "detail": "Checking attraction categories and exact place details."},
            {"stage": "building", "message": "Preparing attraction cards", "detail": "Adding ratings, locations and photos."},
        ]
    if intent == "hotel":
        return base + [
            {"stage": "hotels", "message": "Finding the best hotels", "detail": "Checking stay options."},
            {"stage": "building", "message": "Preparing hotel suggestions", "detail": "Formatting results."},
        ]
    if intent == "restaurant":
        return base + [
            {"stage": "restaurants", "message": "Looking for great restaurants", "detail": "Matching food preferences."},
            {"stage": "building", "message": "Preparing restaurant suggestions", "detail": "Formatting results."},
        ]
    if intent == "weather":
        return base + [
            {"stage": "weather", "message": "Checking the latest weather", "detail": "Getting weather context."},
            {"stage": "building", "message": "Preparing weather answer", "detail": "Formatting forecast details."},
        ]
    if intent == "transport":
        return base + [
            {"stage": "transport", "message": "Searching travel options", "detail": "Checking route and ticket context."},
            {"stage": "building", "message": "Preparing transport options", "detail": "Formatting results."},
        ]
    return base + [
        {"stage": "routing", "message": "Choosing the right travel agents", "detail": "Routing the request."},
        {"stage": "building", "message": "Almost ready", "detail": "Preparing the final answer."},
    ]


def analyze_chat_flow(question: str, active_flow: bool = False) -> ChatFlowPlan:
    intent, confidence, reason = classify_intent(question)
    entities = extract_basic_entities(question)
    lower = normalize_query(question)

    if intent == "recommendation" and entities.get("destination"):
        if re.search(r"\b(?:in|within|around)\s+", lower):
            entities["target_region"] = entities["destination"]

    should_start_trip = intent == "itinerary"
    should_use_direct_rag = intent == "knowledge"
    should_reset_questionnaire = active_flow and intent in {"knowledge", "recommendation", "attraction", "hotel", "restaurant", "weather", "transport"}

    # Short replies inside a questionnaire are field values, not standalone
    # knowledge requests. Explicit questions/openers can still exit the flow.
    explicit_information_request = lower.startswith(RAG_OPENERS) or "?" in question
    if active_flow and len(lower.split()) <= 3 and not explicit_information_request:
        should_use_direct_rag = False
        should_reset_questionnaire = False

    if intent == "transport" and any(term in lower for term in ["confirmation number", "pnr", "boarding pass", "e-ticket", "booking reference"]):
        should_use_direct_rag = False
        should_reset_questionnaire = False

    return ChatFlowPlan(
        intent=intent,
        confidence=confidence,
        destination=entities.get("destination"),
        entities=entities,
        should_use_direct_rag=should_use_direct_rag,
        should_start_trip=should_start_trip,
        should_reset_questionnaire=should_reset_questionnaire,
        reason=reason,
        loader_stages=build_loader_stages(intent),
    )
