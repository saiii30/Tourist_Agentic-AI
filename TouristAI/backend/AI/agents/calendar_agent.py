import os
import sqlite3
import json
from rag_service import client

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
        
        # Strip markdown code blocks if the model returned them
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
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tourist_ai.db"))
    places = []
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return []
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Case insensitive query for city name
        cursor.execute(
            "SELECT name, place_type, description, rating FROM places WHERE LOWER(city) = ? OR LOWER(city) LIKE ?",
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
        conn.close()
    except Exception as e:
        print(f"Error querying database for city '{city}': {e}")
    return places

def calendar_agent(question: str, city: str = "None", days: int = 3, interests: str = "None", travel_style: str = "None", budget: str = "None", other_agent_info: str = "") -> str:
    if city == "None":
        return "I can help you build a personalized day plan, but I need to know your destination first."
        
    city_clean = city.strip().lower()
    budget_clean = budget.strip().lower() if budget else "budget"
    
    # Extract list of lowercase interests
    interests_list = []
    if interests and interests.lower() != "none":
        interests_list = [i.strip().lower() for i in interests.split(",")]
        
    # Map to database budget levels
    budget_val = "Budget"
    if "moderate" in budget_clean:
        budget_val = "Moderate"
    elif "luxury" in budget_clean:
        budget_val = "Luxury"
        
    # LLM Builder: Orchestrate the calendar dynamically using insights from peer agents.
    places = get_db_places(city)
    places_str = ""
    if places:
        for idx, p in enumerate(places, 1):
            places_str += f"{idx}. {p['name']} ({p['type']}) - Rating: {p['rating']}\n   Description: {p['description']}\n"
            
    prompt = (
        f"You are a professional travel planner agent. The user wants a day-by-day travel calendar/itinerary.\n"
        f"Request: '{question}'\n"
        f"Destination City: {city}\n"
        f"Duration: {days} Day(s)\n"
        f"Travel Style: {travel_style}\n"
        f"Interests: {interests}\n"
        f"Budget Category: {budget}\n\n"
        "Guidelines:\n"
        "- The itinerary must respect the budget constraint. "
        "If budget category is 'Budget', prioritize free attractions, budget street foods or low-cost dining, and local/public transport. "
        "If budget category is 'Moderate', mix mid-range experiences, comfortable local transport (like autos or cabs), and nice local restaurants. "
        "If budget category is 'Luxury', prioritize high-end experiences, private chauffeur tours, fine dining, and exclusive activities.\n\n"
    )
    
    if places:
        prompt += (
            "We have these local attractions and dining spots in our database for this city. "
            "Please prioritize including these places in the itinerary/schedule where appropriate:\n"
            f"{places_str}\n"
        )
    else:
        prompt += (
            "We don't have database records for this city. "
            f"Please generate a highly realistic, accurate, and appealing day-by-day itinerary/calendar for {city} "
            f"using your general knowledge.\n"
        )
        
    if other_agent_info:
        prompt += (
            "\nIMPORTANT: Your colleague agents have already suggested the following places/hotels/restaurants. "
            "You MUST incorporate their specific suggestions into your day-by-day schedule to avoid contradictions!\n"
            f"{other_agent_info}\n\n"
        )
        
    prompt += (
        "Construct a detailed day-by-day calendar schedule. For each day, include:\n"
        "- Morning (approx. 09:00 - 12:00) activity/attraction\n"
        "- Afternoon (approx. 14:00 - 17:00) activity/attraction\n"
        "- Evening (approx. 18:00 - 21:00) dining/relaxation or local market stroll\n\n"
        "Return the output STRICTLY as a JSON list of objects, matching this schema:\n"
        "[\n"
        "  {\n"
        "    \"day\": 1,\n"
        "    \"start_time\": \"09:00\",\n"
        "    \"end_time\": \"12:00\",\n"
        "    \"activity\": \"Activity Name\",\n"
        "    \"location\": \"Location expected\",\n"
        "    \"category\": \"Sightseeing\",\n"
        "    \"restaurant\": null,\n"
        "    \"hotel\": null,\n"
        "    \"notes\": \"Details...\"\n"
        "  }\n"
        "]\n\n"
        "Do not output markdown. Output ONLY a valid JSON list."
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
        return content
    except Exception as e:
        print(f"Error calling Groq for calendar fallback: {e}")
        return f"Sorry, I could not generate a travel itinerary calendar for {city} at this moment."
