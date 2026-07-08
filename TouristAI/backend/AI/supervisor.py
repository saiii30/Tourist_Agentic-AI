import re
import json
import os
from database.postgres import PostgresDatabase
from rag_service import client

def init_guided_db():
    PostgresDatabase.initialize()

def save_itinerary_to_db(itinerary_text: str, trip_name: str = None) -> dict:
    prompt = (
        "Analyze the following travel itinerary markdown and extract all calendar events. "
        "For each event, extract: \n"
        "1. The day number (integer, e.g. 1 for Day 1).\n"
        "2. The time slot ('Morning', 'Afternoon', or 'Evening').\n"
        "3. The time range (e.g. '9:00 AM - 12:00 PM', or default to slot times if not specified).\n"
        "4. The name of the activity/attraction.\n"
        "5. Brief details or description of the activity.\n\n"
        "Also determine a suitable unified name for this trip (e.g. 'Madurai 3-Day Tour').\n\n"
        "Return the output strictly in the following JSON format and absolutely nothing else:\n"
        "{\n"
        "  \"trip_name\": \"Name of the trip\",\n"
        "  \"events\": [\n"
        "    {\n"
        "      \"day_num\": 1,\n"
        "      \"time_slot\": \"Morning\",\n"
        "      \"time_range\": \"9:00 AM - 12:00 PM\",\n"
        "      \"activity\": \"Activity Name\",\n"
        "      \"details\": \"Activity Details\"\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Only return raw valid JSON. Do not include markdown code block syntax (like ```json).\n\n"
        f"Itinerary Markdown:\n{itinerary_text}"
    )
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        if "{" in content:
            content = content[content.find("{"):content.rfind("}")+1]
            
        data = json.loads(content)
        trip_name = trip_name or data.get("trip_name", "My Travel Trip")
        events = data.get("events", [])
        
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        
        # Delete old events for this trip name if they exist, to avoid duplicates
        cursor.execute("DELETE FROM calendar_events WHERE trip_name = %s", (trip_name,))
        
        for ev in events:
            cursor.execute(
                "INSERT INTO calendar_events (trip_name, day_num, time_slot, time_range, activity, details) VALUES (%s, %s, %s, %s, %s, %s)",
                (trip_name, ev.get("day_num"), ev.get("time_slot"), ev.get("time_range"), ev.get("activity"), ev.get("details"))
            )
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Successfully saved {len(events)} events for '{trip_name}' to the database.",
            "trip_name": trip_name
        }
    except Exception as e:
        print(f"Error saving calendar events: {e}")
        return {
            "success": False,
            "message": f"Failed to save itinerary events: {str(e)}"
        }

def get_guided_state() -> dict:
    init_guided_db()
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM guided_trip_state")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {row[0]: row[1] for row in rows}

def update_guided_state(key: str, value: str):
    init_guided_db()
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO guided_trip_state (key, value) VALUES (%s, %s)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """, (key, str(value)))
    conn.commit()
    cursor.close()
    conn.close()

def clear_guided_state():
    init_guided_db()
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM guided_trip_state")
    conn.commit()
    cursor.close()
    conn.close()

def extract_query_details(question: str) -> dict:
    prompt = (
        "Analyze the following user query and extract: \n"
        "1. The destination city or location (e.g. 'Chennai', 'Madurai', 'Ooty').\n"
        "2. The duration of the trip (number of days as an integer, default to 3 if not specified).\n"
        "3. A boolean flag 'requires_city' indicating if the user's intent is to get location-specific trip plans/itineraries, weather reports, hotel recommendations, restaurant recommendations, or sightseeing attractions (which require a location to be resolved).\n\n"
        "Return the output strictly in the following JSON format and nothing else:\n"
        "{\n"
        "  \"city\": \"Name of the city (or 'None' if not specified or unclear)\",\n"
        "  \"days\": 3,\n"
        "  \"requires_city\": true\n"
        "}\n\n"
        "Do not include any explanation, backticks, or other formatting. Only valid JSON.\n\n"
        f"Query: {question}"
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
        city = data.get("city", "None")
        if not city or city.lower() == "none":
            city = "None"
        return {
            "city": city,
            "days": int(data.get("days", 3)),
            "requires_city": bool(data.get("requires_city", True))
        }
    except Exception as e:
        print(f"Error in extract_query_details: {e}")
        return {"city": "None", "days": 3, "requires_city": True}

def extract_all_opening_details(question: str) -> dict:
    prompt = (
        "Analyze the following user query and extract any travel details mentioned. "
        "Return the output strictly in the following JSON format and nothing else:\n"
        "{\n"
        "  \"destination\": \"Name of the city or 'None' if not specified\",\n"
        "  \"travel_date\": \"Date/timeframe or 'None' if not specified\",\n"
        "  \"days\": \"Number of days as integer or 'None' if not specified\",\n"
        "  \"budget\": \"'Budget', 'Moderate', 'Luxury', or 'None' if not specified\",\n"
        "  \"travelers\": \"Number of travelers as integer or 'None' if not specified\",\n"
        "  \"travel_style\": \"'Family', 'Solo', 'Friends', 'Couple', 'Business', or 'None' if not specified\",\n"
        "  \"interests\": \"Comma-separated interests (from 'History', 'Nature', 'Adventure', 'Food', 'Photography', 'Shopping') or 'None' if not specified\"\n"
        "}\n\n"
        "Do not include any explanation, backticks, or other formatting. Only valid JSON.\n\n"
        f"Query: {question}"
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
        return {
            "destination": data.get("destination", "None"),
            "travel_date": data.get("travel_date", "None"),
            "days": data.get("days", "None"),
            "budget": data.get("budget", "None"),
            "travelers": data.get("travelers", "None"),
            "travel_style": data.get("travel_style", "None"),
            "interests": data.get("interests", "None")
        }
    except Exception as e:
        print(f"Error in extract_all_opening_details: {e}")
        return {
            "destination": "None",
            "travel_date": "None",
            "days": "None",
            "budget": "None",
            "travelers": "None",
            "travel_style": "None",
            "interests": "None"
        }

def extract_single_field(field_key: str, user_response: str) -> str:
    user_response_clean = user_response.strip().lower()
    
    # --- Local Rule-Based / Regex Parsing ---
    if field_key == "destination":
        # Check if the response matches any city in our json database
        db_path = os.path.join(os.path.dirname(__file__), "agents", "locations_data.json")
        if os.path.exists(db_path):
            try:
                with open(db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for city in data.keys():
                    if city in user_response_clean:
                        return city.title()
            except Exception:
                pass
                
    elif field_key == "travel_date":
        # If response is simple/short, just return it title-cased
        words = user_response_clean.split()
        if len(words) <= 3:
            return user_response.strip().title()
            
    elif field_key in ["days", "travelers"]:
        # Extract first digit sequence
        nums = re.findall(r'\b\d+\b', user_response_clean)
        if nums:
            return nums[0]
        word_map = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"}
        for word, num_str in word_map.items():
            if word in user_response_clean:
                return num_str
                
    elif field_key == "budget":
        # Check numbers
        nums = re.findall(r'\b\d+\b', user_response_clean.replace(",", ""))
        if nums:
            val = int(nums[0])
            if val <= 5000:
                return "Budget"
            elif val <= 15000:
                return "Moderate"
            else:
                return "Luxury"
        # Keyword matches
        if any(w in user_response_clean for w in ["budget", "cheap", "low", "affordable", "below 5000", "under 5000", "economy"]):
            return "Budget"
        if any(w in user_response_clean for w in ["moderate", "medium", "mid", "average", "normal", "between 5000", "5000 to 15000"]):
            return "Moderate"
        if any(w in user_response_clean for w in ["luxury", "high", "expensive", "premium", "rich", "above 15000", "over 15000"]):
            return "Luxury"
            
    elif field_key == "travel_style":
        for style in ["family", "solo", "friends", "couple", "business"]:
            if style in user_response_clean:
                return style.capitalize()
        if "friend" in user_response_clean:
            return "Friends"
        if "partner" in user_response_clean or "spouse" in user_response_clean or "husband" in user_response_clean or "wife" in user_response_clean or "honeymoon" in user_response_clean:
            return "Couple"
        if "kid" in user_response_clean or "child" in user_response_clean or "parent" in user_response_clean or "family" in user_response_clean:
            return "Family"
        if "alone" in user_response_clean or "myself" in user_response_clean:
            return "Solo"
        if "work" in user_response_clean or "meeting" in user_response_clean or "office" in user_response_clean:
            return "Business"
            
    elif field_key == "interests":
        matched = []
        possible_interests = ["history", "nature", "adventure", "food", "photography", "shopping"]
        for interest in possible_interests:
            if interest in user_response_clean:
                matched.append(interest.capitalize())
        if "historical" in user_response_clean or "temple" in user_response_clean or "monument" in user_response_clean or "palace" in user_response_clean or "museum" in user_response_clean:
            matched.append("History")
        if "trek" in user_response_clean or "hike" in user_response_clean or "climb" in user_response_clean or "raft" in user_response_clean or "sport" in user_response_clean:
            matched.append("Adventure")
        if "beach" in user_response_clean or "waterfall" in user_response_clean or "park" in user_response_clean or "lake" in user_response_clean or "forest" in user_response_clean:
            matched.append("Nature")
        if "eat" in user_response_clean or "dining" in user_response_clean or "restaurant" in user_response_clean or "cuisine" in user_response_clean:
            matched.append("Food")
        if "photo" in user_response_clean or "camera" in user_response_clean or "scenic" in user_response_clean or "views" in user_response_clean:
            matched.append("Photography")
        if "market" in user_response_clean or "bazaar" in user_response_clean or "shop" in user_response_clean:
            matched.append("Shopping")
            
        if matched:
            return ", ".join(list(set(matched)))
            
    # --- LLM Fallback (if rule-based parsing fails) ---
    if field_key == "destination":
        prompt = (
            f"Extract the destination city name from this user response: '{user_response}'. "
            "Return ONLY the city name in plain text (e.g. 'Hampi') and absolutely nothing else. "
            "If no destination is clear, return 'None'."
        )
    elif field_key == "travel_date":
        prompt = (
            f"Extract the travel date or timeframe from this user response: '{user_response}'. "
            "Return the date description in plain text (e.g. 'Next Saturday') and absolutely nothing else. "
            "If not clear, return 'None'."
        )
    elif field_key == "days":
        prompt = (
            f"Extract the number of days of travel from this user response: '{user_response}'. "
            "Return ONLY the number as an integer (e.g. '2') and absolutely nothing else. "
            "If not clear, return 'None'."
        )
    elif field_key == "budget":
        prompt = (
            f"The user was asked their budget. Response: '{user_response}'. "
            "Map this response to one of these categories: 'Budget', 'Moderate', 'Luxury'. "
            "Rules: < 5000 is 'Budget', 5000-15000 is 'Moderate', > 15000 is 'Luxury'. "
            "Return ONLY the category name ('Budget', 'Moderate', 'Luxury') and absolutely nothing else."
        )
    elif field_key == "travelers":
        prompt = (
            f"Extract the number of people traveling from this user response: '{user_response}'. "
            "Return ONLY the number as an integer (e.g. '3') and absolutely nothing else. "
            "If not clear, return 'None'."
        )
    elif field_key == "travel_style":
        prompt = (
            f"The user was asked their travel style. Response: '{user_response}'. "
            "Map it strictly to one of: 'Family', 'Solo', 'Friends', 'Couple', 'Business'. "
            "Return ONLY the category name and absolutely nothing else."
        )
    elif field_key == "interests":
        prompt = (
            f"Extract special interests from this user response: '{user_response}'. "
            "Choose any matching items from: 'History', 'Nature', 'Adventure', 'Food', 'Photography', 'Shopping'. "
            "Return them as a comma-separated list (e.g. 'History, Photography') and absolutely nothing else. "
            "If none match, return 'None'."
        )
    else:
        return user_response

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return response.choices[0].message.content.strip().strip("'\"")
    except Exception as e:
        print(f"Error in extract_single_field fallback: {e}")
        return "None"

def matches_keywords(question, keywords):
    question_lower = question.lower()
    for kw in keywords:
        kw_lower = kw.lower()
        pattern = r'\b' + re.escape(kw_lower) + r'\b'
        if re.search(pattern, question_lower):
            return True
    return False

def get_next_missing_field(g_state: dict) -> tuple[str, str]:
    fields = [
        ("destination", "Great! I'll help you plan your trip. First, where would you like to go?"),
        ("travel_date", "Great choice! When are you planning to travel?"),
        ("days", "How many days are you planning to stay?"),
        ("budget", "What's your approximate budget?\n\n• **Budget** (< ₹5,000)\n• **Moderate** (₹5,000–₹15,000)\n• **Luxury** (> ₹15,000)"),
        ("travelers", "How many people are travelling?"),
        ("travel_style", "What kind of trip do you prefer?\n\n• **Family**\n• **Solo**\n• **Friends**\n• **Couple**\n• **Business**"),
        ("interests", "Any special interests?\n\n• **History**\n• **Nature**\n• **Adventure**\n• **Food**\n• **Photography**\n• **Shopping**")
    ]
    for key, prompt in fields:
        val = g_state.get(key)
        if not val or val == "None":
            return key, prompt
    return None, None

def route_question(state, details=None):
    question = state["question"].strip()
    question_lower = question.lower()

    # Escape guided planning if a new single-topic query is asked
    is_single_topic = any(kw in question_lower for kw in ["weather", "forecast", "climate", "temperature", "rain", "hotel", "stay", "resort", "restaurant", "food", "eat", "cafe", "attraction", "sightseeing", "places to visit", "things to do"])
    if is_single_topic:
        update_guided_state("is_active", "0")
        update_guided_state("awaiting_preview_action", "0")

    # Move general question check to the very top to bypass planning triggers
    if details and not details.get("requires_city", True):
        return ["general"]

    # 1. Start Trip Planning triggers (detect any of these keywords to initiate flow)
    start_keywords = [
        "trip", "plan", "itinerary", "vacation", "holiday", "tour", "reset", "start over"
    ]
    is_start = matches_keywords(question_lower, start_keywords)
    
    if not is_start:
        if not is_single_topic:
            if details is None:
                details = extract_query_details(question)
            if details.get("city") != "None" and details.get("requires_city", True):
                is_start = True

    g_state = get_guided_state()
    is_active = g_state.get("is_active") == "1"

    if is_start:
        # Start or reset guided flow
        clear_guided_state()
        update_guided_state("is_active", "1")
        
        # Parse initial query details
        extracted = extract_all_opening_details(question)
        for k, v in extracted.items():
            if v != "None":
                update_guided_state(k, v)
                
        # Re-fetch state
        g_state = get_guided_state()
        missing_key, missing_prompt = get_next_missing_field(g_state)
        
        if missing_key:
            return ["merge"]
        else:
            # Everything provided in the first sentence
            update_guided_state("is_active", "0")
            update_guided_state("awaiting_preview_action", "1")
            return ["hotel", "restaurant", "nearby", "weather", "calendar"]

    # 2. Google Calendar Sync Response Routing
    if g_state.get("awaiting_google_sync") == "1":
        return ["google_calendar"]

    # 3. Preview Action Response Routing (only checked if not starting a new trip)
    if g_state.get("awaiting_preview_action") == "1":
        if question_lower in ["1", "save", "save itinerary", "yes", "yep", "sure", "please"]:
            return ["save_itinerary"]
        elif question_lower in ["3", "regenerate", "regenerate itinerary", "different", "another", "redo"]:
            return ["regenerate_itinerary"]
        elif question_lower in ["delete", "delete itinerary", "delete trip", "discard"]:
            return ["delete_itinerary"]
        else:
            # Default to modify for natural language modification inputs (like replacing attractions)
            return ["modify_itinerary"]
            
    elif is_active:
        # User is answering questions
        missing_key, missing_prompt = get_next_missing_field(g_state)
        
        if missing_key:
            # Save response to the active missing field
            val = extract_single_field(missing_key, question)
            if val != "None":
                update_guided_state(missing_key, val)
                
        g_state = get_guided_state()
        next_key, next_prompt = get_next_missing_field(g_state)
        
        if next_key:
            return ["merge"]
        else:
            # Complete!
            update_guided_state("is_active", "0")
            update_guided_state("awaiting_preview_action", "1")
            return ["hotel", "restaurant", "nearby", "weather", "calendar"]

    # Default stateless routing

    routes = []

    # Restaurant Agent
    if matches_keywords(question_lower, [
        "restaurant", "food", "eat", "idli", "dosa", "breakfast", "lunch", "dinner"
    ]):
        routes.append("restaurant")

    # Hotel Agent
    if matches_keywords(question_lower, [
        "hotel", "stay", "room", "resort", "accommodation"
    ]):
        routes.append("hotel")

    # Nearby Places Agent
    if matches_keywords(question_lower, [
        "nearby", "place", "tourist", "visit", "attraction", "temple", "sightseeing"
    ]):
        routes.append("nearby")

    # Weather Agent
    if matches_keywords(question_lower, [
        "weather", "rain", "temperature", "forecast", "climate", "umbrella", 
        "sunny", "wind", "humidity", "hot", "cold"
    ]):
        routes.append("weather")

    # Calendar Agent
    if matches_keywords(question_lower, [
        "calendar", "schedule", "itinerary", "timetable", "agenda", 
        "plan my day", "day plan", "day-by-day", "time slot"
    ]):
        routes.append("calendar")

    # Remove duplicates
    routes = list(set(routes))

    # Default agent if nothing matches
    if not routes:
        routes.append("general")

    return routes