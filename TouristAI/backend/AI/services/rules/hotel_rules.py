import re
from typing import Optional

def extract_hotel_type(text: str) -> Optional[str]:
    lower = text.lower()
    types = {
        "resort": "Resort",
        "villa": "Villa",
        "homestay": "Homestay",
        "business hotel": "Business Hotel",
        "business": "Business Hotel"
    }
    for keyword, name in types.items():
        if re.search(r"\b" + re.escape(keyword) + r"\b", lower):
            return name
    return None

def extract_amenities(text: str) -> Optional[str]:
    lower = text.lower()
    amenities = []
    mappings = [
        ("pool", "Pool"),
        ("swimming", "Pool"),
        ("parking", "Parking"),
        ("garage", "Parking"),
        ("wi-fi", "Wi-Fi"),
        ("wifi", "Wi-Fi"),
        ("internet", "Wi-Fi"),
        ("spa", "Spa"),
        ("massage", "Spa"),
        ("pet", "Pet Friendly"),
        ("dog", "Pet Friendly"),
        ("cat", "Pet Friendly")
    ]
    for word, label in mappings:
        if re.search(r"\b" + re.escape(word) + r"s?\b", lower) and label not in amenities:
            amenities.append(label)
            
    if amenities:
        return ", ".join(amenities)
    return None
