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

def calendar_agent(question: str, city: str = "None", days: int = 3, interests: str = "None", travel_style: str = "None", budget: str = "None") -> str:
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
        
    # 1. Attempt programmatic schedule assembly from local database
    db_path = os.path.join(os.path.dirname(__file__), "locations_data.json")
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            city_data = data.get(city_clean)
            if city_data:
                # Hotels (for accommodation notes)
                matched_hotels = [h for h in city_data.get("hotels", []) if h.get("budget") == budget_val]
                if len(matched_hotels) < 3:
                    matched_hotels += [h for h in city_data.get("hotels", []) if h not in matched_hotels]
                selected_hotel = matched_hotels[0]["name"] if matched_hotels else "Local Hotel"
                
                # Restaurants (sorted by interest match)
                def score_restaurant(r):
                    r_interests = [ri.lower() for ri in r.get("interests", [])]
                    return len(set(interests_list).intersection(set(r_interests)))
                
                matched_rests = [r for r in city_data.get("restaurants", []) if r.get("budget") == budget_val]
                matched_rests.sort(key=score_restaurant, reverse=True)
                if len(matched_rests) < 3:
                    others = [r for r in city_data.get("restaurants", []) if r not in matched_rests]
                    others.sort(key=score_restaurant, reverse=True)
                    matched_rests += others
                    
                # Attractions/Places (sorted by interest match)
                def score_place(p):
                    p_interests = [pi.lower() for pi in p.get("interests", [])]
                    return len(set(interests_list).intersection(set(p_interests)))
                    
                matched_places = list(city_data.get("nearby_places", []))
                matched_places.sort(key=score_place, reverse=True)
                
                # Build Day-by-Day schedule
                lines = []
                for day in range(1, days + 1):
                    lines.append(f"### Day {day}")
                    
                    # Morning (approx. 9:00 AM - 12:00 PM) - Attraction
                    if matched_places:
                        place = matched_places[(day - 1) % len(matched_places)]
                        lines.append(f"**Morning (9:00 AM - 12:00 PM)**\n**Visit the {place['name']}**\n\n{place['description']} Best time to visit: {place['best_time'].lower()}.")
                    else:
                        lines.append(f"**Morning (9:00 AM - 12:00 PM)**\nExplore the local scenic sights and viewpoints around the city.")
                        
                    # Lunch
                    if matched_rests:
                        rest = matched_rests[(day * 2 - 2) % len(matched_rests)]
                        lines.append(f"\n### Lunch\nHead to **{rest['name']}** for a delicious lunch of {rest['cuisine'].lower()} cuisine (approx. {rest['price']}). Recommended: *{rest['must_try']}*.")
                    else:
                        lines.append(f"\n### Lunch\nEnjoy lunch at a local cafe or restaurant.")
                        
                    # Afternoon (approx. 1:00 PM - 5:00 PM) - Second Attraction
                    if matched_places and len(matched_places) > 1:
                        place = matched_places[day % len(matched_places)]
                        lines.append(f"\n**Afternoon (1:00 PM - 5:00 PM)**\n**Explore {place['name']}**\n\n{place['description']} Enjoy the local sights and capture scenic views.")
                    else:
                        lines.append(f"\n**Afternoon (1:00 PM - 5:00 PM)**\nRelax and unwind or stroll near your hotel, **{selected_hotel}**.")
                        
                    # Evening (approx. 6:00 PM - 9:00 PM) - Dinner / Stroll
                    if matched_rests and len(matched_rests) > 1:
                        rest = matched_rests[(day * 2 - 1) % len(matched_rests)]
                        lines.append(f"\n**Evening (6:00 PM - 9:00 PM)**\n**Relax at local beach/viewpoint and enjoy dinner**\n\nHave dinner at **{rest['name']}** ({rest['cuisine']} style). Try their famous *{rest['must_try']}* while enjoying the evening atmosphere.")
                    else:
                        lines.append(f"\n**Evening (6:00 PM - 9:00 PM)**\nEnjoy a pleasant evening walk in the local market, and dine at a cozy nearby eatery.")
                        
                    lines.append("") # Empty line between days
                    
                return "\n".join(lines)
        except Exception as e:
            print(f"Error programmatically generating calendar: {e}")
            
    # 2. LLM Fallback (for uncatalogued cities)
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
            f"We don't have database records for {city}. "
            f"Please generate a highly realistic, accurate, and appealing day-by-day itinerary/calendar for {city} "
            f"using your general knowledge.\n"
        )
        
    prompt += (
        "Construct a detailed day-by-day calendar schedule. For each day, include:\n"
        "- Morning (approx. 9:00 AM - 12:00 PM) activity/attraction\n"
        "- Afternoon (approx. 1:00 PM - 5:00 PM) activity/attraction\n"
        "- Evening (approx. 6:00 PM - 9:00 PM) dining/relaxation or local market stroll\n\n"
        "Format the output beautifully in Markdown. Make sure each day's schedule is clear and easy to read. "
        "Recommend specific dining/food choices for breakfast, lunch, and dinner. "
        "Tailor the spots and activities to match the traveler's interests and travel style.\n"
        "Keep the tone encouraging, helpful, and professional."
    )
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling Groq for calendar fallback: {e}")
        return f"Sorry, I could not generate a travel itinerary calendar for {city} at this moment."
