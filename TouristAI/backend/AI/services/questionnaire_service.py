import re
import os
import sys
import json
import datetime
from typing import Any, Dict, Optional, Tuple

# Ensure parent directory is in path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.rules import common_rules, hotel_rules, restaurant_rules, calendar_rules, attraction_rules
try:
    from rag_service import client
except ImportError:
    client = None

AGENT_ROUTE_MAP = {
    "attraction": "nearby",
    "nearby": "nearby",
    "hotel": "hotel",
    "restaurant": "restaurant",
    "calendar": "calendar",
    "budget": "budget",
}

def normalize_agent(agent: str) -> str:
    if agent == "nearby":
        return "attraction"
    return agent

def route_for_agent(agent: str) -> str:
    return AGENT_ROUTE_MAP.get(normalize_agent(agent), agent)

def state_key(agent: str, field_key: str) -> str:
    return f"{normalize_agent(agent)}.{field_key}"

# Helper fields extractors for registry
def extract_hotel_fields(text: str) -> dict:
    extracted = {}
    city = common_rules.extract_city(text)
    if city: extracted["city"] = city
    budget = common_rules.extract_budget(text)
    if budget: extracted["budget"] = budget
    checkin, checkout = common_rules.extract_dates(text)
    if checkin: extracted["checkin"] = checkin
    if checkout: extracted["checkout"] = checkout
    guests = common_rules.extract_guest_count(text)
    if guests: extracted["guests"] = str(guests)
    breakfast = common_rules.extract_boolean_preferences(text, "breakfast")
    if breakfast: extracted["breakfast"] = breakfast
    h_type = hotel_rules.extract_hotel_type(text)
    if h_type: extracted["hotel_type"] = h_type
    amenities = hotel_rules.extract_amenities(text)
    if amenities: extracted["amenities"] = amenities
    return extracted

def extract_restaurant_fields(text: str) -> dict:
    extracted = {}
    city = common_rules.extract_city(text)
    if city: extracted["city"] = city
    budget = common_rules.extract_budget(text)
    if budget: extracted["budget_per_person"] = budget
    diet = restaurant_rules.extract_diet(text)
    if diet: extracted["diet"] = diet
    cuisine = restaurant_rules.extract_cuisine(text)
    if cuisine: extracted["cuisine"] = cuisine
    meal = restaurant_rules.extract_meal(text)
    if meal: extracted["meal_time"] = meal
    family = restaurant_rules.extract_family_friendly(text)
    if family: extracted["family_friendly"] = family
    outdoor = restaurant_rules.extract_outdoor_seating(text)
    if outdoor: extracted["outdoor_seating"] = outdoor
    allergies = restaurant_rules.extract_allergies(text)
    if allergies: extracted["allergies"] = allergies
    return extracted

def extract_attraction_fields(text: str) -> dict:
    extracted = {}
    city = common_rules.extract_city(text)
    if city: extracted["city"] = city
    t_type = attraction_rules.extract_traveler_type(text)
    if t_type: extracted["traveler_type"] = t_type
    # Attempt days extraction
    days = common_rules.extract_guest_count(text)
    if days and "day" in text.lower():
        extracted["days"] = str(days)
    dist = attraction_rules.extract_max_distance(text)
    if dist: extracted["max_distance"] = dist
    price = attraction_rules.extract_price_preference(text)
    if price: extracted["price_preference"] = price
    interests = attraction_rules.extract_interests(text)
    if interests: extracted["interests"] = interests
    return extracted

def extract_calendar_fields(text: str) -> dict:
    extracted = {}
    city = common_rules.extract_city(text)
    if city: extracted["destination"] = city
    checkin, checkout = common_rules.extract_dates(text)
    if checkin: extracted["travel_date"] = checkin
    days = common_rules.extract_guest_count(text)
    if days and "day" in text.lower():
        extracted["days"] = str(days)
    travelers = common_rules.extract_guest_count(text)
    if travelers and any(w in text.lower() for w in ["people", "person", "guest", "adult", "traveler"]):
        extracted["travelers"] = str(travelers)
    budget = common_rules.extract_budget(text)
    if budget: extracted["budget"] = budget
    style = attraction_rules.extract_traveler_type(text)
    if style: extracted["travel_style"] = style
    interests = attraction_rules.extract_interests(text)
    if interests: extracted["interests"] = interests
    cal_prefs = calendar_rules.extract_calendar_preferences(text)
    extracted.update(cal_prefs)
    return extracted

def extract_budget_fields(text: str) -> dict:
    extracted = {}
    city = common_rules.extract_city(text)
    if city: extracted["city"] = city
    days = common_rules.extract_guest_count(text)
    if days and "day" in text.lower():
        extracted["days"] = str(days)
    travelers = common_rules.extract_guest_count(text)
    if travelers and any(w in text.lower() for w in ["people", "person", "guest", "adult", "traveler"]):
        extracted["travelers"] = str(travelers)
    budget = common_rules.extract_budget(text)
    if budget: extracted["budget_level"] = budget
    for key in ["include_hotel", "include_transport", "shopping_budget"]:
        pref = common_rules.extract_boolean_preferences(text, key)
        if pref: extracted[key] = pref
    return extracted

# Validation rules for validation layer
def validate_field(field_key: str, value: str) -> bool:
    if not value or value == "None" or value == "":
        return False
    value_clean = value.strip().title() if isinstance(value, str) else value
    value_lower = value.strip().lower() if isinstance(value, str) else ""
    
    # Skip / Any support
    if value_lower in {"any", "skip", "no preference", "don't care", "dont care", "none", "i don't care"}:
        return True
        
    if field_key in {"budget", "budget_level", "budget_per_person"}:
        return value_clean in {"Budget", "Moderate", "Luxury"}
    if field_key in {"breakfast", "family_friendly", "outdoor_seating", "free_time", "shopping", "nightlife", "google_calendar", "include_hotel", "include_transport", "shopping_budget"}:
        return value_clean in {"Yes", "No"}
    if field_key == "hotel_type":
        return value_clean in {"Resort", "Villa", "Homestay", "Business Hotel"}
    if field_key == "diet":
        return value_clean in {"Vegetarian", "Non-vegetarian"}
    if field_key in {"guests", "travelers", "days"}:
        try:
            int(value)
            return True
        except ValueError:
            return False
    if field_key in {"checkin", "checkout", "travel_date"}:
        # Accept YYYY-MM-DD or any string representing a date that isn't empty/None
        return True
    return True

AGENT_REGISTRY = {
    "hotel": {
        "fields": ["city", "budget", "checkin", "checkout", "guests", "breakfast", "hotel_type", "amenities"],
        "priority": ["city", "checkin", "checkout", "guests", "budget", "breakfast", "hotel_type", "amenities"],
        "extractor": extract_hotel_fields,
        "prompts": {
            "city": "Great! I'll help you find the right hotel. Which city are you looking in?",
            "checkin": "What is your check-in date?",
            "checkout": "What is your check-out date?",
            "guests": "How many guests?",
            "budget": "What is your hotel budget?\n\n* **Budget**\n* **Moderate**\n* **Luxury**",
            "breakfast": "Do you need breakfast included?\n\n* **Yes**\n* **No**",
            "hotel_type": "Preferred hotel type?\n\n* **Resort**\n* **Villa**\n* **Homestay**\n* **Business Hotel**",
            "amenities": "Any required amenities?\n\n* **Pool**\n* **Parking**\n* **Wi-Fi**\n* **Spa**\n* **Pet Friendly**"
        }
    },
    "restaurant": {
        "fields": ["city", "budget_per_person", "diet", "cuisine", "meal_time", "family_friendly", "outdoor_seating", "allergies"],
        "priority": ["city", "budget_per_person", "diet", "cuisine", "meal_time", "family_friendly", "outdoor_seating", "allergies"],
        "extractor": extract_restaurant_fields,
        "prompts": {
            "city": "Which city should I search restaurants in?",
            "budget_per_person": "What is your budget per person?\n\n* **Budget**\n* **Moderate**\n* **Luxury**",
            "diet": "Vegetarian or non-vegetarian?",
            "cuisine": "Any preferred cuisine?\n\n* **South Indian**\n* **North Indian**\n* **Chinese**\n* **Italian**\n* **Continental**\n* **Seafood**\n* **Local**\n* **Street Food**\n* **Cafe**",
            "meal_time": "Breakfast, lunch, or dinner?",
            "family_friendly": "Need family-friendly restaurants?\n\n* **Yes**\n* **No**",
            "outdoor_seating": "Prefer outdoor seating?\n\n* **Yes**\n* **No**",
            "allergies": "Any allergies or food restrictions? Type **None** if there are no restrictions."
        }
    },
    "attraction": {
        "fields": ["city", "days", "interests", "max_distance", "price_preference", "traveler_type"],
        "priority": ["city", "days", "interests", "max_distance", "price_preference", "traveler_type"],
        "extractor": extract_attraction_fields,
        "prompts": {
            "city": "Which city or destination do you want attractions for?",
            "days": "How many days do you have?",
            "interests": "What type of places do you like?\n\n* **Nature**\n* **Adventure**\n* **History**\n* **Photography**\n* **Shopping**\n* **Kids Friendly**\n* **Senior Citizen Friendly**",
            "max_distance": "Maximum travel distance from your stay?\n\n* **Within 5 km**\n* **Within 10 km**\n* **Within 25 km**\n* **No limit**",
            "price_preference": "Do you prefer free places, paid attractions, or both?",
            "traveler_type": "Who is travelling?\n\n* **Solo**\n* **Couple**\n* **Family**\n* **Friends**\n* **Senior Citizens**"
        }
    },
    "calendar": {
        "fields": ["destination", "travel_date", "days", "budget", "travelers", "travel_style", "interests", "start_time", "end_time", "free_time", "shopping", "nightlife", "google_calendar"],
        "priority": ["destination", "travel_date", "days", "budget", "travelers", "travel_style", "interests", "start_time", "end_time", "free_time", "shopping", "nightlife", "google_calendar"],
        "extractor": extract_calendar_fields,
        "prompts": {
            "destination": "Where would you like to go?",
            "travel_date": "When are you planning to travel?",
            "days": "How many days?",
            "budget": "What is your budget?\n\n* **Budget**\n* **Moderate**\n* **Luxury**",
            "travelers": "How many travelers?",
            "travel_style": "What kind of trip?\n\n* **Family**\n* **Solo**\n* **Friends**\n* **Couple**\n* **Business**",
            "interests": "Any interests?\n\n* **Nature**\n* **Adventure**\n* **History**\n* **Food**\n* **Photography**\n* **Shopping**\n* **Kids Friendly**\n* **Senior Citizen Friendly**",
            "start_time": "What time do you prefer to start each day? (e.g. 09:00 AM)",
            "end_time": "What time do you prefer to end each day? (e.g. 06:00 PM)",
            "free_time": "Do you want free time included?\n\n* **Yes**\n* **No**",
            "shopping": "Should I include shopping time?\n\n* **Yes**\n* **No**",
            "nightlife": "Should I include nightlife options?\n\n* **Yes**\n* **No**",
            "google_calendar": "Do you want Google Calendar sync after the itinerary is created?\n\n* **Yes**\n* **No**",
        }
    },
    "budget": {
        "fields": ["city", "days", "travelers", "budget_level", "include_hotel", "include_transport", "shopping_budget"],
        "priority": ["city", "days", "travelers", "budget_level", "include_hotel", "include_transport", "shopping_budget"],
        "extractor": extract_budget_fields,
        "prompts": {
            "city": "Which city is your trip for?",
            "days": "How many days is the trip?",
            "travelers": "How many travelers?",
            "budget_level": "What budget level do you prefer?\n\n* **Budget**\n* **Moderate**\n* **Luxury**",
            "include_hotel": "Should I include hotel cost?\n\n* **Yes**\n* **No**",
            "include_transport": "Should I include local transport cost?\n\n* **Yes**\n* **No**",
            "shopping_budget": "Do you want to include shopping budget?\n\n* **Yes**\n* **No**",
        }
    }
}

AGENT_SCHEMAS = AGENT_REGISTRY # Alias for naming compatibility

def get_questionnaire(agent: str) -> list[dict]:
    agent = normalize_agent(agent)
    config = AGENT_REGISTRY.get(agent)
    if not config:
        return []
    # Map registry config to old return list structure for backwards compatibility
    return [{"key": field, "prompt": config["prompts"][field]} for field in config["priority"]]

def get_next_missing_field(agent: str, g_state: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
    agent = normalize_agent(agent)
    config = AGENT_REGISTRY.get(agent)
    if not config:
        return None, None
        
    for field in config["priority"]:
        value = g_state.get(state_key(agent, field))
        if not value or value == "None" or value == "":
            prompt = config["prompts"][field]
            return field, prompt
            
    return None, None

def build_context(agent: str, g_state: Dict[str, str]) -> Dict[str, str]:
    agent = normalize_agent(agent)
    context = {}
    config = AGENT_REGISTRY.get(agent)
    if config:
        for field in config["fields"]:
            context[field] = g_state.get(state_key(agent, field), "None")
    return context

def extract_values_with_llm(agent: str, question: str) -> dict:
    agent = normalize_agent(agent)
    config = AGENT_REGISTRY.get(agent)
    if not config or not client:
        return {}
        
    schema_desc = {}
    for f in config["fields"]:
        schema_desc[f] = f"Value for '{f}' field. Valid values might be specified in the prompt: {config['prompts'][f]}"
        
    schema_json = json.dumps(schema_desc, indent=2)
    prompt = (
        f"Analyze the user message and extract travel preferences for the '{agent}' agent "
        f"based on the schema below. Only extract fields defined in the schema. Do not guess or invent details if they are not explicitly or clearly implied in the message.\n\n"
        f"Schema:\n{schema_json}\n\n"
        f"User Message: \"{question}\"\n\n"
        f"Instructions:\n"
        f"1. Extract values for schema keys ONLY if they are mentioned or clearly implied in the message.\n"
        f"2. Values must be clean strings or numbers.\n"
        f"3. Return ONLY a valid JSON object containing the extracted fields and their values. "
        f"Do not include any explanation, backticks, or markdown formatting (no ```json). E.g. {{\"field\": \"value\"}}."
    )
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        if "{" in content:
            content = content[content.find("{"):content.rfind("}")+1]
            
        data = json.loads(content)
        validated = {}
        for k, v in data.items():
            if k in config["fields"] and v is not None and str(v).lower() != "none" and str(v).strip() != "":
                validated[k] = str(v)
        return validated
    except Exception as e:
        print(f"Error in extract_values_with_llm: {e}")
        return {}

def extract_initial_values(agent: str, question: str) -> Dict[str, str]:
    agent = normalize_agent(agent)
    config = AGENT_REGISTRY.get(agent)
    if not config:
        return {}
        
    # Smart Hybrid Extraction Flow:
    # 1. Run local agent-specific rule extraction
    extracted = config["extractor"](question)
    
    # 2. Filter and Validate rule extraction
    validated = {}
    for k, v in extracted.items():
        if validate_field(k, v):
            validated[k] = v
            
    # Check if any required fields are missing
    missing_fields = [f for f in config["fields"] if f not in validated]
    word_count = len(question.split())
    
    # 3. Groq LLM Fallback (Only run if missing required fields and input is complex (> 4 words))
    if missing_fields and word_count > 4:
        print(f"[INFO] Invoking Groq LLM fallback for {agent} extraction (word count={word_count})")
        llm_extracted = extract_values_with_llm(agent, question)
        for k, v in llm_extracted.items():
            if k in missing_fields and validate_field(k, v):
                validated[k] = v
                
    return validated

def parse_field(agent: str, field_key: str, text: str) -> str:
    # Rule-based fallback parse for a single field
    agent = normalize_agent(agent)
    
    # Check for direct Skip/Any support
    text_lower = text.strip().lower()
    if text_lower in {"skip", "any", "no preference", "don't care", "dont care", "none", "i don't care"}:
        return "Any"
        
    if field_key in {"city", "destination"}:
        city = common_rules.extract_city(text)
        return city if city else "None"
    if field_key in {"checkin", "checkout", "travel_date"}:
        checkin, checkout = common_rules.extract_dates(text)
        if field_key == "checkin" and checkin: return checkin
        if field_key == "checkout" and checkout: return checkout
        if field_key == "travel_date" and checkin: return checkin
        return "None"
    if field_key in {"guests", "travelers", "days"}:
        guests = common_rules.extract_guest_count(text)
        return str(guests) if guests else "None"
    if field_key in {"budget", "budget_level", "budget_per_person"}:
        budget = common_rules.extract_budget(text)
        return budget if budget else "None"
    if field_key == "hotel_type":
        h_type = hotel_rules.extract_hotel_type(text)
        return h_type if h_type else "None"
    if field_key == "amenities":
        amenities = hotel_rules.extract_amenities(text)
        return amenities if amenities else "None"
    if field_key == "diet":
        diet = restaurant_rules.extract_diet(text)
        return diet if diet else "None"
    if field_key == "cuisine":
        cuisine = restaurant_rules.extract_cuisine(text)
        return cuisine if cuisine else "None"
    if field_key == "meal_time":
        meal = restaurant_rules.extract_meal(text)
        return meal if meal else "None"
    if field_key in {"breakfast", "family_friendly", "outdoor_seating", "free_time", "shopping", "nightlife", "google_calendar", "include_hotel", "include_transport", "shopping_budget"}:
        val = common_rules.extract_boolean_preferences(text, field_key)
        return val if val else "None"
    if field_key == "allergies":
        allergies = restaurant_rules.extract_allergies(text)
        return allergies if allergies else "None"
        
    return text.strip() or "None"

def get_progress_metadata(agent: str, g_state: Dict[str, str]) -> dict:
    agent = normalize_agent(agent)
    config = AGENT_REGISTRY.get(agent)
    if not config:
        return {}
        
    fields = config["fields"]
    total = len(fields)
    completed = 0
    for field in fields:
        value = g_state.get(state_key(agent, field))
        if value and value != "None" and value != "":
            completed += 1
            
    progress = int((completed / total) * 100) if total > 0 else 0
    return {
        "agent": agent,
        "completed": completed,
        "total": total,
        "progress": progress
    }

def save_agent_answer(agent_name: str, field_key: str, answer: str):
    agent_name = normalize_agent(agent_name)
    config = AGENT_REGISTRY.get(agent_name)
    if not config:
        return
        
    # Check for direct Skip/Any support
    answer_lower = answer.strip().lower()
    if answer_lower in {"skip", "any", "no preference", "don't care", "dont care", "none", "i don't care"}:
        from supervisor import update_guided_state
        update_guided_state(state_key(agent_name, field_key), "Any")
        return

    # Smart Extraction Flow on the answer text:
    # 1. Run local agent-specific rule extraction
    extracted = config["extractor"](answer)
    
    # 2. If the active field is not extracted, fallback to parse_field rule
    if field_key not in extracted:
        parsed = parse_field(agent_name, field_key, answer)
        if parsed and parsed != "None":
            extracted[field_key] = parsed
            
    # 3. If field is still missing and user answer is complex (> 4 words), call LLM fallback
    word_count = len(answer.split())
    if field_key not in extracted and word_count > 4:
        llm_extracted = extract_values_with_llm(agent_name, answer)
        if field_key in llm_extracted:
            extracted[field_key] = llm_extracted[field_key]
            
    # 4. If the field is STILL missing, but it's a valid non-empty answer,
    # save the raw answer (fallback) to prevent stuck loops
    if field_key not in extracted and answer.strip():
        extracted[field_key] = answer.strip()
        
    # 5. Validate and save all extracted fields to SQLite
    from supervisor import update_guided_state
    for k, v in extracted.items():
        if k in config["fields"] and validate_field(k, v):
            update_guided_state(state_key(agent_name, k), v)