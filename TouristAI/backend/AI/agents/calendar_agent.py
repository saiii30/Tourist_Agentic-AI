import os
import json
from database.postgres import PostgresDatabase
from rag_service import client
from agents.calendar_builder import CalendarBuilder


def demo_log(step: str, message: str) -> None:
    print(f"[LOG][{step}] {message}")


def demo_names(items, name_key: str = "name", limit: int = 3) -> str:
    if not items:
        return "none"
    names = []
    for item in items[:limit]:
        if isinstance(item, dict):
            names.append(str(item.get(name_key) or item.get("title") or item.get("activity") or "Unnamed"))
    return ", ".join(names) if names else "none"

def extract_trip_details(question: str) -> tuple[str, int]:
    prompt = (
        "Analyze the following user query and extract: \n"
        "1. The destination city or location.\n"
        "2. The duration of the trip (number of days as an integer).\n\n"
        "Return the output strictly in the following JSON format and nothing else:\n"
        "{\n"
        "  \"city\": \"Name of the city (or 'None' if not specified)\",\n"
        "  \"days\": 3\n"
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
        city_extracted = data.get("city", "None")
        if city_extracted.lower() == "none" or not city_extracted:
            city_extracted = "None"
        return city_extracted, int(data.get("days", 3))
    except Exception as e:
        print(f"Error extracting trip details: {e}")
        return "None", 3

def get_db_places(city: str) -> list:
    places = []
    try:
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, place_type, description, rating FROM places WHERE LOWER(city) = %s OR LOWER(city) LIKE %s",
            (city.lower(), f"%{city.lower()}%")
        )
        rows = cursor.fetchall()
        for row in rows:
            places.append({
                "name": row[0],
                "type": row[1],
                "description": row[2],
                "rating": row[3]
            })
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error querying database for city '{city}': {e}")
    return places

# Instant structured data generators
def generate_hotels(city: str) -> list:
    from services.trip_service import get_structured_hotels
    return get_structured_hotels(city, "Moderate")

def generate_restaurants(city: str) -> list:
    from services.trip_service import get_structured_restaurants
    return get_structured_restaurants(city, "Moderate")

def generate_attractions(city: str) -> list:
    from services.trip_service import get_structured_attractions
    return get_structured_attractions(city, "Moderate")

def _extract_agent_data(result) -> list:
    if not isinstance(result, dict):
        return []
    data = result.get("data")
    return data if isinstance(data, list) else []

def _load_cached_agent_data(key: str) -> list:
    try:
        import json
        from supervisor import get_guided_state
        raw = get_guided_state().get(key)
        if not raw:
            return []
        data = json.loads(raw) if isinstance(raw, str) else raw
        return data if isinstance(data, list) else []
    except Exception:
        return []

def _load_hotels_google_first(question: str, city: str, budget: str, days: int) -> list:
    try:
        from agents.hotel_agent import hotel_agent
        demo_log("CALENDAR_FALLBACK_HOTELS", "No upstream hotel data. Calling Hotel Agent first.")
        result = hotel_agent(
            question=question,
            city=city,
            budget=budget,
            travelers=1,
        )
        data = _extract_agent_data(result)
        if data:
            demo_log(
                "CALENDAR_FALLBACK_HOTELS",
                f"Hotel Agent returned source={result.get('source', 'unknown')}, count={len(data)}, sample={demo_names(data)}"
            )
            return data
    except Exception as e:
        print(f"[WARNING] Hotel Agent failed while preparing calendar data: {e}")

    from services.trip_service import get_structured_hotels
    data = get_structured_hotels(city, budget)
    demo_log("CALENDAR_FALLBACK_HOTELS", f"LLM/TripService fallback count={len(data)}, sample={demo_names(data)}")
    return data

def _load_restaurants_google_first(question: str, city: str, budget: str, interests: str) -> list:
    try:
        from agents.restaurant_agent import restaurant_agent
        demo_log("CALENDAR_FALLBACK_RESTAURANTS", "No upstream restaurant data. Calling Restaurant Agent first.")
        result = restaurant_agent(
            question=question,
            city=city,
            interests=interests,
            budget=budget,
        )
        data = _extract_agent_data(result)
        if data:
            demo_log(
                "CALENDAR_FALLBACK_RESTAURANTS",
                f"Restaurant Agent returned source={result.get('source', 'unknown')}, count={len(data)}, sample={demo_names(data)}"
            )
            return data
    except Exception as e:
        print(f"[WARNING] Restaurant Agent failed while preparing calendar data: {e}")

    from services.trip_service import get_structured_restaurants
    data = get_structured_restaurants(city, budget)
    demo_log("CALENDAR_FALLBACK_RESTAURANTS", f"LLM/TripService fallback count={len(data)}, sample={demo_names(data)}")
    return data

def _load_attractions_google_first(question: str, city: str, budget: str, interests: str) -> list:
    try:
        from agents.nearby_agent import nearby_agent
        demo_log("CALENDAR_FALLBACK_ATTRACTIONS", "No upstream attraction data. Calling Nearby Agent first.")
        result = nearby_agent(question, city, interests)
        data = _extract_agent_data(result)
        if data:
            demo_log(
                "CALENDAR_FALLBACK_ATTRACTIONS",
                f"Nearby Agent returned source={result.get('source', 'unknown')}, count={len(data)}, sample={demo_names(data)}"
            )
            return data
    except Exception as e:
        print(f"[WARNING] Nearby Agent failed while preparing calendar data: {e}")

    from services.trip_service import get_structured_attractions
    data = get_structured_attractions(city, budget)
    demo_log("CALENDAR_FALLBACK_ATTRACTIONS", f"LLM/TripService fallback count={len(data)}, sample={demo_names(data)}")
    return data

def calendar_agent(
    question: str,
    city: str = "None",
    days: int = 3,
    interests: str = "None",
    travel_style: str = "None",
    budget: str = "None",
    hotels_data: list = None,
    restaurants_data: list = None,
    nearby_data: list = None,
    weather_data: dict = None,
    other_agent_info: str = "",
    transport_data: list = None
) -> str:
    """
    Orchestrator calendar agent that coordinates data preparation and invokes CalendarBuilder.
    """
    print(f"[DEBUG] Calendar Agent received hotels_data: {len(hotels_data or [])} items")
    print(f"[DEBUG] Calendar Agent received restaurants_data: {len(restaurants_data or [])} items")
    print(f"[DEBUG] Calendar Agent received nearby_data: {len(nearby_data or [])} items")
    demo_log(
        "CALENDAR_START",
        (
            f"city={city}, days={days}, budget={budget}, style={travel_style}, interests={interests}, "
            f"upstream_hotels={len(hotels_data or [])}, upstream_restaurants={len(restaurants_data or [])}, "
            f"upstream_attractions={len(nearby_data or [])}, weather={'yes' if weather_data else 'no'}, "
            f"transport={len(transport_data or [])}"
        )
    )

    if city == "None" or not city or city == "":
        extracted_city, _ = extract_trip_details(question)
        if extracted_city != "None":
            city = extracted_city
        else:
            return "I can help you build a personalized day plan, but I need to know your destination first."

    # Check for regeneration count in guided state
    try:
        from supervisor import get_guided_state
        g_state = get_guided_state()
        regen_count = int(g_state.get("regen_count", 0))
    except Exception:
        regen_count = 0

    # Validate and handle empty structured data by asking each proper agent first.
    # Those agents use Google Places as the primary data source and fall back only
    # when the API is unavailable or returns no usable data.
    if not hotels_data:
        hotels_data = _load_cached_agent_data("hotels_data")
    if not hotels_data:
        hotels_data = _load_hotels_google_first(question, city, budget, days)
    else:
        demo_log("CALENDAR_USE_HOTELS", f"Using upstream hotels count={len(hotels_data)}, sample={demo_names(hotels_data)}")
    if not restaurants_data:
        restaurants_data = _load_cached_agent_data("restaurants_data")
    if not restaurants_data:
        restaurants_data = _load_restaurants_google_first(question, city, budget, interests)
    else:
        demo_log("CALENDAR_USE_RESTAURANTS", f"Using upstream restaurants count={len(restaurants_data)}, sample={demo_names(restaurants_data)}")
    if not nearby_data:
        nearby_data = _load_cached_agent_data("nearby_data")
    if not nearby_data:
        nearby_data = _load_attractions_google_first(question, city, budget, interests)
    else:
        demo_log("CALENDAR_USE_ATTRACTIONS", f"Using upstream attractions count={len(nearby_data)}, sample={demo_names(nearby_data)}")

    # Rotate lists based on regen_count to choose alternative items programmatically
    if regen_count > 0:
        print(f"[INFO] Programmatic regeneration rotation active (offset={regen_count})")
        if hotels_data:
            offset = regen_count % len(hotels_data)
            hotels_data = hotels_data[offset:] + hotels_data[:offset]
        if restaurants_data:
            offset = regen_count % len(restaurants_data)
            restaurants_data = restaurants_data[offset:] + restaurants_data[:offset]
        if nearby_data:
            offset = regen_count % len(nearby_data)
            nearby_data = nearby_data[offset:] + nearby_data[:offset]

    if not weather_data:
        weather_data = {"main": "Clear", "temp": 28.0}
        demo_log("CALENDAR_WEATHER", "No upstream weather data. Using default clear-weather fallback.")
    else:
        demo_log("CALENDAR_WEATHER", f"Using upstream weather data: {str(weather_data)[:180]}")

    # Extract real parameters from guided state
    try:
        from supervisor import get_guided_state
        g_state = get_guided_state()
        travel_date = g_state.get("calendar.travel_date", g_state.get("travel_date", "2026-07-12"))
        
        # Safe integer cast for travelers count
        raw_travelers = g_state.get("calendar.travelers", g_state.get("travelers", 4))
        try:
            travelers = int(raw_travelers)
        except ValueError:
            travelers = 4
            
        current_location = g_state.get("calendar.current_location", g_state.get("current_location", "None"))
        travel_mode = g_state.get("calendar.travel_mode", g_state.get("travel_mode", "None"))
        diet = g_state.get("calendar.diet", g_state.get("diet", "None"))
    except Exception:
        travel_date = "2026-07-12"
        travelers = 4
        current_location = "None"
        travel_mode = "None"
        diet = "None"

    # Invoke programmatic builder
    itinerary_struct = CalendarBuilder.build_itinerary(
        city=city,
        start_date_str=travel_date,
        days=days,
        budget=budget,
        travel_style=travel_style,
        interests=interests,
        travelers=travelers,
        hotels=hotels_data,
        restaurants=restaurants_data,
        attractions=nearby_data,
        weather=weather_data,
        current_location=current_location,
        travel_mode=travel_mode,
        diet=diet,
        transport_data=transport_data
    )
    day_count = len(itinerary_struct.get("days", [])) if isinstance(itinerary_struct, dict) else 0
    demo_log(
        "CALENDAR_BUILD",
        (
            f"CalendarBuilder received hotels={len(hotels_data or [])}, restaurants={len(restaurants_data or [])}, "
            f"attractions={len(nearby_data or [])}, transport={len(transport_data or [])}, built_days={day_count}"
        )
    )

    # Flatten the day-by-day structure into the flat list layout expected by the system
    flat_itinerary = []
    for day_info in itinerary_struct.get("days", []):
        day_num = day_info.get("day")
        for activity in day_info.get("activities", []):
            # Create a compatibility dictionary matching the output schema
            flat_item = {
                "day": day_num,
                "start_time": activity.get("start_time"),
                "end_time": activity.get("end_time"),
                "activity": activity.get("title"),
                "location": activity.get("location"),
                "category": activity.get("category"),
                "restaurant": activity.get("title") if activity.get("category") == "Food" else None,
                "hotel": activity.get("title") if activity.get("category") == "Hotel" else None,
                "notes": activity.get("notes"),
                "activity_id": activity.get("activity_id"),
                "google_event_id": activity.get("google_event_id"),
                "hotel_id": activity.get("hotel_id"),
                "restaurant_id": activity.get("restaurant_id"),
                "attraction_id": activity.get("attraction_id"),
                "latitude": activity.get("latitude"),
                "longitude": activity.get("longitude"),
                "start_datetime": activity.get("start_datetime"),
                "end_datetime": activity.get("end_datetime"),
                "travel_time": activity.get("travel_time"),
                "transport": activity.get("transport"),
                "estimated_cost": activity.get("estimated_cost"),
                "googlePhotoName": activity.get("googlePhotoName"),
                "status": activity.get("status")
            }
            flat_itinerary.append(flat_item)

    demo_log(
        "CALENDAR_FLATTEN",
        f"flat_items={len(flat_itinerary)}, sample={demo_names(flat_itinerary, name_key='activity', limit=6)}"
    )
    return json.dumps(flat_itinerary, indent=2)
