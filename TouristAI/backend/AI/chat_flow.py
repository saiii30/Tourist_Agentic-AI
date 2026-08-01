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
}

INTENT_KEYWORDS = {
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
    for key, destination in KNOWN_DESTINATIONS.items():
        if key in lower:
            return destination
    return None


def extract_basic_entities(question: str) -> Dict[str, str]:
    lower = normalize_query(question)
    entities: Dict[str, str] = {}
    destination = infer_destination(question)
    if destination:
        entities["destination"] = destination

    days_match = re.search(r"\b(\d{1,2})\s*(?:day|days)\b", lower)
    if days_match:
        entities["days"] = days_match.group(1)

    travelers_match = re.search(r"\b(\d{1,2})\s*(?:people|person|persons|traveller|travellers|traveler|travelers)\b", lower)
    if travelers_match:
        entities["travelers"] = travelers_match.group(1)

    budget_match = re.search(r"(?:rs\.?|₹|inr)\s*([0-9,]+)", lower)
    if budget_match:
        entities["budget_amount"] = budget_match.group(1).replace(",", "")
    elif any(word in lower for word in ["low budget", "cheap", "budget friendly"]):
        entities["budget"] = "Low"
    elif "luxury" in lower:
        entities["budget"] = "Luxury"
    elif "moderate" in lower:
        entities["budget"] = "Moderate"

    return entities


def classify_intent(question: str) -> tuple[str, float, str]:
    lower = normalize_query(question)
    scores = {intent: 0 for intent in INTENT_KEYWORDS}
    for intent, keywords in INTENT_KEYWORDS.items():
        scores[intent] = sum(1 for keyword in keywords if keyword_matches(lower, keyword))

    if any(phrase in lower for phrase in RAG_KNOWLEDGE_PHRASES):
        return "knowledge", 0.9, "matched knowledge phrase"

    if lower.startswith(RAG_OPENERS) and infer_destination(question):
        return "knowledge", 0.75, "informational opener with destination"

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

    should_start_trip = intent == "itinerary"
    should_use_direct_rag = intent == "knowledge"
    should_reset_questionnaire = active_flow and intent in {"knowledge", "hotel", "restaurant", "weather", "transport"}

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
