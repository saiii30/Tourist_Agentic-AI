import re
import datetime
import dateparser
from typing import Optional, Tuple
from rapidfuzz import process, fuzz

POPULAR_CITIES = [
    "Ooty", "Goa", "Madurai", "Chennai", "Bangalore", "Mysore", "Munnar", 
    "Hampi", "Kochi", "Hyderabad", "Delhi", "Mumbai", "Jaipur", "Agra", 
    "Udaipur", "Manali", "Shimla", "Dharamshala", "Rishikesh", "Varanasi", 
    "Pondicherry", "Kolkata", "Pune", "Alleppey", "Wayanad", "Coorg", "Kodaikanal"
]

def extract_city(text: str) -> Optional[str]:
    # Normalize text
    text_clean = text.strip()
    words = re.findall(r"\b[a-zA-Z]+\b", text_clean)
    
    # 1. Check for exact case-insensitive matches in popular cities
    for word in words:
        for city in POPULAR_CITIES:
            if word.lower() == city.lower():
                return city
                
    # 2. Try fuzzy matching each word against popular cities
    for word in words:
        if len(word) >= 3:
            match = process.extractOne(word, POPULAR_CITIES, scorer=fuzz.WRatio)
            if match and match[1] >= 85:
                return match[0]
                
    # 3. Fallback to pattern matching
    pattern = re.compile(r"\b(?:in|at|to|for)\s+([A-Za-z][A-Za-z\s]{1,30})(?=\s|$|,|\.|\?)", re.IGNORECASE)
    match = pattern.search(text_clean)
    if match:
        city_candidate = match.group(1).strip()
        city_candidate = re.sub(r"\b(hotel|hotels|restaurant|restaurants|places|attractions|budget|trip|itinerary|with)\b", "", city_candidate, flags=re.IGNORECASE).strip()
        if city_candidate and len(city_candidate) >= 3:
            return city_candidate.title()
            
    return None

def clean_date_text(text: str) -> str:
    # Remove numbers related to guests, travelers, rooms
    text = re.sub(r"\b\d+\s*(?:guests?|people|adults?|children|kids?|persons?|rooms?)\b", "", text, flags=re.IGNORECASE)
    # Remove common agent keywords to isolate date terms
    text = re.sub(r"\b(?:luxury|moderate|budget|resort|villa|homestay|hotel|breakfast|pool|wifi|spa|pet friendly)\b", "", text, flags=re.IGNORECASE)
    return text.strip()

def extract_dates(text: str) -> Tuple[Optional[str], Optional[str]]:
    text_clean = clean_date_text(text).lower()
    today = datetime.date.today()
    
    if text_clean == "today":
        return today.strftime("%Y-%m-%d"), None
    elif text_clean == "tomorrow":
        tomorrow = today + datetime.timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d"), None
        
    split_patterns = [r"\bto\b", r"\buntil\b", r"\bthrough\b", r"-"]
    for pattern in split_patterns:
        parts = re.split(pattern, text_clean, flags=re.IGNORECASE)
        if len(parts) >= 2:
            part1 = parts[0].strip()
            part2 = parts[1].strip()
            part1 = re.sub(r"\bfrom\b", "", part1, flags=re.IGNORECASE).strip()
            
            d1 = dateparser.parse(part1, settings={'PREFER_DATES_FROM': 'future'})
            d2 = dateparser.parse(part2, settings={'PREFER_DATES_FROM': 'future'})
            
            if d1 and d2:
                if d1.year < today.year:
                    d1 = d1.replace(year=today.year)
                if d2.year < today.year:
                    d2 = d2.replace(year=today.year)
                if d2.date() < d1.date():
                    d2 = d2.replace(year=d1.year + 1)
                return d1.strftime("%Y-%m-%d"), d2.strftime("%Y-%m-%d")
            elif d1:
                return d1.strftime("%Y-%m-%d"), None
            elif d2:
                return None, d2.strftime("%Y-%m-%d")
                
    d = dateparser.parse(text_clean, settings={'PREFER_DATES_FROM': 'future'})
    if d:
        if d.year < today.year:
            d = d.replace(year=today.year)
        return d.strftime("%Y-%m-%d"), None
        
    return None, None

def extract_budget(text: str) -> Optional[str]:
    lower = text.lower()
    nums = re.findall(r"\b\d+\b", lower.replace(",", ""))
    if nums:
        val = int(nums[0])
        if val <= 5000:
            return "Budget"
        elif val <= 15000:
            return "Moderate"
        else:
            return "Luxury"
            
    budget_keywords = ["budget", "cheap", "low", "affordable", "economy", "pocket friendly", "less expensive"]
    moderate_keywords = ["moderate", "medium", "mid", "average", "normal", "decent", "reasonable"]
    luxury_keywords = ["luxury", "premium", "expensive", "high", "fancy", "5 star", "five star", "best", "top", "expensive"]
    
    if any(w in lower for w in budget_keywords):
        return "Budget"
    if any(w in lower for w in moderate_keywords):
        return "Moderate"
    if any(w in lower for w in luxury_keywords):
        return "Luxury"
        
    return None

def extract_guest_count(text: str) -> Optional[int]:
    lower = text.lower()
    patterns = [
        r"(\d+)\s*(?:guests?|people|adults?|persons?|travelers?)",
        r"(?:group of|for|with)\s*(\d+)",
        r"(\d+)\s*guests?"
    ]
    for pattern in patterns:
        match = re.search(pattern, lower)
        if match:
            return int(match.group(1))
            
    word_map = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "solo": 1, "couple": 2
    }
    for word, val in word_map.items():
        if re.search(r"\b" + re.escape(word) + r"\b", lower):
            return val
            
    digits = re.findall(r"\b\d+\b", lower)
    if digits:
        return int(digits[0])
        
    return None

def extract_boolean_preferences(text: str, field_key: str = None) -> Optional[str]:
    lower = text.lower()
    # Direct Skip check
    if any(w in lower for w in ["skip", "any", "no preference", "don't care", "dont care", "i don't care"]):
        return "Any"
    if any(w in lower for w in ["yes", "yeah", "yep", "sure", "need", "include", "with", "want"]):
        return "Yes"
    if any(w in lower for w in ["no", "nope", "not", "without", "dont", "don't", "no need"]):
        return "No"
    return None
