import re
from typing import Optional

def extract_max_distance(text: str) -> Optional[str]:
    lower = text.lower()
    nums = re.findall(r"\b\d+\b", lower)
    if nums:
        val = int(nums[0])
        return f"Within {val} km"
    if any(w in lower for w in ["no limit", "any distance", "unlimited", "no boundary", "anywhere"]):
        return "No limit"
    return None

def extract_price_preference(text: str) -> Optional[str]:
    lower = text.lower()
    if "both" in lower or "any" in lower or "either" in lower:
        return "Both"
    if "free" in lower or "no ticket" in lower or "unpaid" in lower:
        return "Free"
    if "paid" in lower or "ticket" in lower or "entry fee" in lower:
        return "Paid"
    return None

def extract_traveler_type(text: str) -> Optional[str]:
    lower = text.lower()
    styles = {
        "solo": "Solo",
        "couple": "Couple",
        "friends": "Friends",
        "family": "Family",
        "senior citizens": "Senior Citizens",
        "senior citizen": "Senior Citizens",
        "seniors": "Senior Citizens",
        "elderly": "Senior Citizens"
    }
    for kw, name in styles.items():
        if kw in lower:
            return name
    return None

def extract_interests(text: str) -> Optional[str]:
    lower = text.lower()
    interests = []
    mappings = [
        ("nature", "Nature"), ("beach", "Nature"), ("waterfall", "Nature"), ("scenic", "Nature"), ("hill", "Nature"),
        ("adventure", "Adventure"), ("trek", "Adventure"), ("hike", "Adventure"), ("rafting", "Adventure"),
        ("history", "History"), ("temple", "History"), ("museum", "History"), ("fort", "History"), ("palace", "History"), ("monument", "History"),
        ("photo", "Photography"), ("camera", "Photography"), ("views", "Photography"),
        ("shopping", "Shopping"), ("market", "Shopping"), ("bazaar", "Shopping"),
        ("food", "Food"), ("dine", "Food"), ("dining", "Food"), ("eat", "Food"),
        ("kid", "Kids Friendly"), ("children", "Kids Friendly"), ("play", "Kids Friendly"),
        ("senior", "Senior Citizen Friendly"), ("parents", "Senior Citizen Friendly"), ("elderly", "Senior Citizen Friendly")
    ]
    for word, label in mappings:
        if word in lower and label not in interests:
            interests.append(label)
            
    if interests:
        return ", ".join(interests)
    return None
