import os
import json
from rag_service import client

def nearby_agent(question, city="None", interests="None"):
    if city == "None":
        return "I need to know which city you are visiting to suggest nearby places."
        
    city_clean = city.strip().lower()
    
    # Extract list of lowercase interests
    interests_list = []
    if interests and interests.lower() != "none":
        interests_list = [i.strip().lower() for i in interests.split(",")]
        
    # Attempt local database lookup
    db_path = os.path.join(os.path.dirname(__file__), "locations_data.json")
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            city_data = data.get(city_clean)
            if city_data and "nearby_places" in city_data:
                # Interest scoring function
                def score_interest(p):
                    p_interests = [pi.lower() for pi in p.get("interests", [])]
                    return len(set(interests_list).intersection(set(p_interests)))
                
                # Sort all nearby places by interest score descending
                matched = list(city_data["nearby_places"])
                matched.sort(key=score_interest, reverse=True)
                matched = matched[:3]
                
                # Format to expected markdown output
                lines = []
                for place in matched:
                    lines.append(f"* **{place['name']}**: {place['description']}")
                    lines.append(f"\t+ Best time to visit: {place['best_time']}")
                return "\n".join(lines)
        except Exception as e:
            print(f"Error loading local nearby places database: {e}")
            
    # Fallback to LLM specific prompt if city not found in local db or database error
    try:
        interests_str = ", ".join(interests_list) if interests_list else "sightseeing"
        prompt = (
            f"Generate a list of 2-3 realistic places to visit / attractions in {city.title()} catering to {interests_str} interests.\n"
            "Format the output strictly as a markdown list with bold names, a brief description, and the best time to visit.\n"
            "Do not include any greeting, introduction, or general trip advice. Return only the markdown list."
        )
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in nearby_agent fallback: {e}")
        return f"Currently, I cannot fetch sightseeing suggestions for {city}."