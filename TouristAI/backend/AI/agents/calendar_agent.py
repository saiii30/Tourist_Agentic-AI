import os
import json
from database.postgres import PostgresDatabase
from rag_service import client
from agents.calendar_builder import CalendarBuilder

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

# Dedicated LLM fallback generators
def generate_hotels(city: str) -> list:
    print(f"[FALLBACK] Calling dedicated fallback generator for hotels in {city}.")
    prompt = (
        f"Generate a list of 5 realistic, actual hotels in the city of {city}.\n"
        "Return the output STRICTLY as a JSON list of objects matching this schema:\n"
        "[\n"
        "  {\n"
        "    \"hotel_id\": \"hotel-1\",\n"
        "    \"name\": \"Grand Palace Hotel\",\n"
        "    \"rating\": 4.6,\n"
        "    \"reviews\": 340,\n"
        "    \"address\": \"123 Palace Road, Central Block\",\n"
        "    \"website\": \"http://grandpalacehotel.com\",\n"
        "    \"latitude\": 17.3850,\n"
        "    \"longitude\": 78.4867,\n"
        "    \"pricePerNight\": 4500,\n"
        "    \"amenities\": [\"Free Wi-Fi\", \"Swimming Pool\", \"Room Service\"],\n"
        "    \"room_types\": [\"Standard\", \"Deluxe\", \"Suite\"],\n"
        "    \"parking\": \"Valet parking available\",\n"
        "    \"photos\": [],\n"
        "    \"booking_url\": \"http://booking.com\"\n"
        "  }\n"
        "]\n"
        "Output only valid JSON. Do not include markdown codeblocks or explanations."
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
        if "[" in content:
            content = content[content.find("["):content.rfind("]")+1]
        return json.loads(content)
    except Exception as e:
        print(f"Error generating fallback hotels: {e}")
        return []

def generate_restaurants(city: str) -> list:
    print(f"[FALLBACK] Calling dedicated fallback generator for restaurants in {city}.")
    prompt = (
        f"Generate a list of 8 realistic, actual restaurants in the city of {city}. Include breakfast cafes as well as lunch/dinner spots.\n"
        "Return the output STRICTLY as a JSON list of objects matching this schema:\n"
        "[\n"
        "  {\n"
        "    \"restaurant_id\": \"rest-1\",\n"
        "    \"name\": \"Chutneys Restaurant\",\n"
        "    \"rating\": 4.4,\n"
        "    \"reviews\": 1200,\n"
        "    \"address\": \"Begumpet, Main Road\",\n"
        "    \"website\": \"http://chutneysrest.com\",\n"
        "    \"latitude\": 17.4410,\n"
        "    \"longitude\": 78.4815,\n"
        "    \"price\": \"Moderate\",\n"
        "    \"serves_breakfast\": true,\n"
        "    \"serves_lunch\": true,\n"
        "    \"serves_dinner\": true,\n"
        "    \"serves_vegetarian\": true,\n"
        "    \"hours\": [\"07:00 AM - 11:00 PM\"]\n"
        "  }\n"
        "]\n"
        "Output only valid JSON. Do not include markdown codeblocks or explanations."
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
        if "[" in content:
            content = content[content.find("["):content.rfind("]")+1]
        return json.loads(content)
    except Exception as e:
        print(f"Error generating fallback restaurants: {e}")
        return []

def generate_attractions(city: str) -> list:
    print(f"[FALLBACK] Calling dedicated fallback generator for attractions in {city}.")
    prompt = (
        f"Generate a list of 10 realistic, actual tourist attractions and sightseeing places in the city of {city}.\n"
        "Return the output STRICTLY as a JSON list of objects matching this schema:\n"
        "[\n"
        "  {\n"
        "    \"attraction_id\": \"attr-1\",\n"
        "    \"name\": \"Golconda Fort\",\n"
        "    \"rating\": 4.7,\n"
        "    \"reviews\": 25000,\n"
        "    \"address\": \"Ibrahim Bagh, Hyderabad\",\n"
        "    \"website\": \"https://golcondafort.com\",\n"
        "    \"latitude\": 17.3833,\n"
        "    \"longitude\": 78.4011,\n"
        "    \"types\": [\"historical_monument\", \"fort\", \"sightseeing\"],\n"
        "    \"hours\": [\"09:00 AM - 05:30 PM\"],\n"
        "    \"editorial\": \"A massive, historic fort famous for its acoustics and architecture.\"\n"
        "  }\n"
        "]\n"
        "Output only valid JSON. Do not include markdown codeblocks or explanations."
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
        if "[" in content:
            content = content[content.find("["):content.rfind("]")+1]
        return json.loads(content)
    except Exception as e:
        print(f"Error generating fallback attractions: {e}")
        return []

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
    other_agent_info: str = ""
) -> str:
    """
    Orchestrator calendar agent that coordinates data preparation and invokes CalendarBuilder.
    """
    print(f"[DEBUG] Calendar Agent received hotels_data: {len(hotels_data or [])} items")
    print(f"[DEBUG] Calendar Agent received restaurants_data: {len(restaurants_data or [])} items")
    print(f"[DEBUG] Calendar Agent received nearby_data: {len(nearby_data or [])} items")

    if city == "None":
        return "I can help you build a personalized day plan, but I need to know your destination first."

    # Check for regeneration count in guided state
    try:
        from supervisor import get_guided_state
        g_state = get_guided_state()
        regen_count = int(g_state.get("regen_count", 0))
    except Exception:
        regen_count = 0

    # Validate and handle empty structured data fallbacks
    if not hotels_data:
        hotels_data = generate_hotels(city)
    if not restaurants_data:
        restaurants_data = generate_restaurants(city)
    if not nearby_data:
        nearby_data = generate_attractions(city)

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

    # Invoke programmatic builder
    itinerary_struct = CalendarBuilder.build_itinerary(
        city=city,
        start_date_str="2026-07-12",  # Default or extract
        days=days,
        budget=budget,
        travel_style=travel_style,
        interests=interests,
        travelers=4,  # Default
        hotels=hotels_data,
        restaurants=restaurants_data,
        attractions=nearby_data,
        weather=weather_data
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
                "status": activity.get("status")
            }
            flat_itinerary.append(flat_item)

    return json.dumps(flat_itinerary, indent=2)
