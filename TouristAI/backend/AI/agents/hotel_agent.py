import os
import json
from rag_service import client

def hotel_agent(question, city="None", budget="None", travelers=1):
    if city == "None":
        return "I need to know which city you are visiting to suggest hotels."
        
    city_clean = city.strip().lower()
    budget_clean = budget.strip().lower() if budget else "budget"
    
    # Map to database budget levels
    budget_val = "Budget"
    if "moderate" in budget_clean:
        budget_val = "Moderate"
    elif "luxury" in budget_clean:
        budget_val = "Luxury"
        
    # Attempt local database lookup
    db_path = os.path.join(os.path.dirname(__file__), "locations_data.json")
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            city_data = data.get(city_clean)
            if city_data and "hotels" in city_data:
                # Filter by budget
                matched = [h for h in city_data["hotels"] if h.get("budget") == budget_val]
                
                # If we don't have enough matched budget hotels, pad with other budgets from the same city
                if len(matched) < 3:
                    others = [h for h in city_data["hotels"] if h.get("budget") != budget_val]
                    matched = (matched + others)[:3]
                else:
                    matched = matched[:3]
                
                # Format to the expected markdown output
                lines = []
                for hotel in matched:
                    lines.append(f"* **{hotel['name']}**: {hotel['price']}")
                    lines.append(f"\t+ {hotel['vibe']}")
                    features_str = ", ".join(hotel['features'])
                    lines.append(f"\t+ {features_str}")
                return "\n".join(lines)
        except Exception as e:
            print(f"Error loading local hotel database: {e}")
            
    # Fallback to LLM specific prompt if city not found in local db or database error
    try:
        prompt = (
            f"Generate a list of 2-3 realistic hotels in {city.title()} matching a {budget_val} budget.\n"
            "Format the output strictly as a markdown list with bold names, estimated prices, and a brief vibe/amenities description.\n"
            "Do not include any greeting, introduction, or general trip advice. Return only the markdown list."
        )
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in hotel_agent fallback: {e}")
        return f"Currently, I cannot fetch hotel recommendations for {city}."