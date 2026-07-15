import re
from typing import Optional

def extract_start_time(text: str) -> Optional[str]:
    lower = text.lower()
    # Check start time patterns: "start at 9:00 AM", "starts around 10 AM", "morning start: 9am"
    patterns = [
        r"\b(?:start|begin|starts|morning)\b.*?\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
        r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b.*?\b(?:start|begin)\b"
    ]
    for pattern in patterns:
        match = re.search(pattern, lower)
        if match:
            return match.group(1).upper()
    return None

def extract_end_time(text: str) -> Optional[str]:
    lower = text.lower()
    # Check end time patterns: "end at 6 PM", "finish by 5pm", "wrap up at 6:00 pm"
    patterns = [
        r"\b(?:end|finish|stop|wrap|ends|evening|night)\b.*?\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
        r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b.*?\b(?:end|finish|stop)\b"
    ]
    for pattern in patterns:
        match = re.search(pattern, lower)
        if match:
            return match.group(1).upper()
    return None

def extract_calendar_preferences(text: str) -> dict:
    lower = text.lower()
    prefs = {}
    
    start = extract_start_time(text)
    if start:
        prefs["start_time"] = start
        
    end = extract_end_time(text)
    if end:
        prefs["end_time"] = end
        
    # Free time, shopping, nightlife, google calendar
    mappings = {
        "free_time": ["free time", "leisure", "relax", "break"],
        "shopping": ["shopping", "markets", "shop", "buy"],
        "nightlife": ["nightlife", "pubs", "clubs", "bars", "party"],
        "google_calendar": ["google calendar", "calendar sync", "sync"]
    }
    
    for key, keywords in mappings.items():
        # Look for yes/no patterns around the keyword
        for kw in keywords:
            if kw in lower:
                # Check negative context
                no_context = any(neg in lower for neg in ["no ", "without", "dont", "don't", "no need"])
                if no_context:
                    prefs[key] = "No"
                else:
                    prefs[key] = "Yes"
                break
                
    return prefs
