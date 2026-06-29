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
            
    # Fallback to get_answer if city not found in local db or database error
    try:
        from rag_service import get_answer
        ans = get_answer(question)
        return ans.get("answer") if isinstance(ans, dict) else ans
    except Exception as e:
        print(f"Error in nearby_agent fallback: {e}")
        return f"Currently, I cannot fetch sightseeing suggestions for {city}."