import re
from typing import Optional

def extract_diet(text: str) -> Optional[str]:
    lower = text.lower()
    if any(w in lower for w in ["non veg", "non-veg", "non vegetarian", "chicken", "meat", "fish", "mutton"]):
        return "Non-vegetarian"
    if any(w in lower for w in ["pure veg", "vegetarian", "veg", "herbal"]):
        return "Vegetarian"
    return None

def extract_cuisine(text: str) -> Optional[str]:
    lower = text.lower()
    cuisines = []
    cuisine_keywords = [
        ("south indian", "South Indian"),
        ("north indian", "North Indian"),
        ("chinese", "Chinese"),
        ("italian", "Italian"),
        ("continental", "Continental"),
        ("seafood", "Seafood"),
        ("local", "Local"),
        ("street food", "Street Food"),
        ("cafe", "Cafe"),
        ("coffee", "Cafe")
    ]
    for kw, label in cuisine_keywords:
        if kw in lower:
            cuisines.append(label)
    if cuisines:
        return ", ".join(cuisines)
    return None

def extract_meal(text: str) -> Optional[str]:
    lower = text.lower()
    meals = []
    for meal in ["breakfast", "lunch", "dinner"]:
        if meal in lower:
            meals.append(meal.title())
    if meals:
        return ", ".join(meals)
    return None

def extract_family_friendly(text: str) -> Optional[str]:
    lower = text.lower()
    if any(w in lower for w in ["family", "kids", "children", "parents", "family friendly"]):
        return "Yes"
    if any(w in lower for w in ["bar", "nightclub", "pub", "romantic", "club"]):
        return "No"
    return None

def extract_outdoor_seating(text: str) -> Optional[str]:
    lower = text.lower()
    if any(w in lower for w in ["outdoor", "garden", "rooftop", "balcony", "view"]):
        return "Yes"
    if "indoor" in lower:
        return "No"
    return None

def extract_allergies(text: str) -> Optional[str]:
    lower = text.lower()
    allergy_match = re.search(r"\ballerg(?:y|ies|ic)\s+(?:to|from)?\s*([a-z\s]+)", lower)
    if allergy_match:
        return allergy_match.group(1).strip()
        
    allergens = ["peanut", "nut", "gluten", "diary", "milk", "egg", "seafood", "fish", "soy", "wheat"]
    found = [alg for alg in allergens if alg in lower]
    if found:
        return ", ".join(found)
        
    if "no allergies" in lower or "none" in lower or "no allergy" in lower:
        return "None"
        
    return None
