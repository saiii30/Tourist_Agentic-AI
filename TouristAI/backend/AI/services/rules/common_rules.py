import re
import datetime
import dateparser
from typing import Optional, Tuple
from rapidfuzz import process, fuzz

POPULAR_CITIES = [
    "Ooty", "Goa", "Madurai", "Chennai", "Bangalore", "Mysore", "Munnar", 
    "Hampi", "Kochi", "Cochin", "Hyderabad", "Delhi", "Mumbai", "Jaipur", "Agra", 
    "Udaipur", "Manali", "Shimla", "Dharamshala", "Rishikesh", "Varanasi", 
    "Pondicherry", "Kolkata", "Pune", "Alleppey", "Wayanad", "Coorg", "Kodaikanal"
]

CITY_ALIASES = {
    "cochin": "Kochi",
}

ACTION_AND_NOISE_WORDS = {
    "visit", "see", "go", "travel", "explore", "places", "things", "attractions", 
    "hotel", "hotels", "restaurant", "restaurants", "trip", "atrip", "itinerary", "budget", "with"
}

def extract_city(text: str, exclude_cities: Optional[list] = None) -> Optional[str]:
    # Normalize text
    text_clean = text.strip()
    words = re.findall(r"\b[a-zA-Z]+\b", text_clean)
    excluded_set = {c.lower() for c in (exclude_cities or []) if c}
    excluded_set.update(ACTION_AND_NOISE_WORDS)
    
    # 1. Check for exact case-insensitive matches in popular cities
    for word in words:
        if word.lower() in excluded_set:
            continue
        for city in POPULAR_CITIES:
            if word.lower() == city.lower():
                return CITY_ALIASES.get(city.lower(), city)
                
    # 2. Try fuzzy matching each word against popular cities
    for word in words:
        if word.lower() in excluded_set:
            continue
        if len(word) >= 3:
            match = process.extractOne(word, POPULAR_CITIES, scorer=fuzz.WRatio)
            if match and match[1] >= 85 and match[0].lower() not in excluded_set:
                return CITY_ALIASES.get(match[0].lower(), match[0])
                
    # 3. Fallback to pattern matching - remove action verb phrases first
    text_for_pattern = re.sub(r"\b(?:to|and|or)\s+(?:visit|see|go|travel|explore)\b", "", text_clean, flags=re.IGNORECASE)
    pattern = re.compile(r"\b(?:in|at|to|for)\s+([A-Za-z][A-Za-z\s]{1,30})(?=\s|$|,|\.|\?)", re.IGNORECASE)
    match = pattern.search(text_for_pattern)
    if match:
        city_candidate = match.group(1).strip()
        city_candidate = re.sub(r"\b(hotel|hotels|restaurant|restaurants|places|attractions|budget|trip|itinerary|with|visit|see|go|travel|explore)\b", "", city_candidate, flags=re.IGNORECASE).strip()
        if city_candidate and len(city_candidate) >= 3 and city_candidate.lower() not in excluded_set:
            return CITY_ALIASES.get(city_candidate.lower(), city_candidate.title())
            
    return None

def clean_date_text(text: str) -> str:
    # Remove numbers related to guests, travelers, rooms
    text = re.sub(r"\b\d+\s*(?:guests?|people|adults?|children|kids?|persons?|rooms?)\b", "", text, flags=re.IGNORECASE)
    # Remove common agent keywords to isolate date terms
    text = re.sub(r"\b(?:luxury|moderate|budget|resort|villa|homestay|hotel|breakfast|pool|wifi|spa|pet friendly)\b", "", text, flags=re.IGNORECASE)
    return text.strip()

def fast_parse_date(s: str):
    if not s or not s.strip():
        return None
    st = s.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(st, fmt)
        except ValueError:
            pass
    try:
        return dateparser.parse(st, languages=['en'], settings={'PREFER_DATES_FROM': 'future'})
    except Exception:
        return None

def extract_dates(text: str) -> Tuple[Optional[str], Optional[str]]:
    date_regex = re.search(r'\b(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b', text)
    if date_regex:
        d_str = date_regex.group(1)
        parsed_d = fast_parse_date(d_str)
        if parsed_d:
            return parsed_d.strftime("%Y-%m-%d"), None

    text_clean = clean_date_text(text).lower()
    
    # Bare numbers should not be parsed as dates
    if text_clean.isdigit():
        return None, None
        
    today = datetime.date.today()
    
    if "tomorrow" in text_clean:
        tomorrow = today + datetime.timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d"), None
    elif "today" in text_clean:
        return today.strftime("%Y-%m-%d"), None
        
    split_patterns = [r"\bto\b", r"\buntil\b", r"\bthrough\b", r"-"]
    for pattern in split_patterns:
        parts = re.split(pattern, text_clean, flags=re.IGNORECASE)
        if len(parts) >= 2:
            part1 = parts[0].strip()
            part2 = parts[1].strip()
            part1 = re.sub(r"\bfrom\b", "", part1, flags=re.IGNORECASE).strip()
            
            d1 = fast_parse_date(part1)
            d2 = fast_parse_date(part2)
            
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
                
    d = fast_parse_date(text_clean)
    if d:
        if d.year < today.year:
            d = d.replace(year=today.year)
        return d.strftime("%Y-%m-%d"), None
        
    return None, None

def extract_budget(text: str) -> Optional[str]:
    lower = text.lower()
    budget_keywords = ["cheap", "low", "affordable", "economy", "budget friendly", "budget-friendly", "pocket friendly", "less expensive"]
    moderate_keywords = ["moderate", "medium", "mid", "average", "normal", "decent", "reasonable"]
    luxury_keywords = ["luxury", "premium", "expensive", "high", "fancy", "5 star", "five star", "best", "top"]

    # Explicit tiers must win over unrelated numbers such as trip duration,
    # traveler count, or year.
    if any(w in lower for w in luxury_keywords):
        return "Luxury"
    if any(w in lower for w in moderate_keywords):
        return "Moderate"
    if any(w in lower for w in budget_keywords):
        return "Low"

    amount_match = re.search(
        r"(?:₹|rs\.?|inr|rupees?|budget\s*(?:of|is|:)?\s*)\s*([0-9][0-9,]*)",
        lower,
    )
    if amount_match:
        val = int(amount_match.group(1).replace(",", ""))
        if val <= 5000:
            return "Low"
        elif val <= 15000:
            return "Moderate"
        else:
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
