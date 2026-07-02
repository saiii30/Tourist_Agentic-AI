import os
import json
from rag_service import client

def restaurant_agent(question, city="None", interests="None", budget="None"):
    if city == "None":
        return "I need to know which city you are visiting to suggest restaurants."
        
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
        
    # Attempt local database lookup
    db_path = os.path.join(os.path.dirname(__file__), "locations_data.json")
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            city_data = data.get(city_clean)
            if city_data and "restaurants" in city_data:
                # Interest scoring function
                def score_interest(r):
                    r_interests = [ri.lower() for ri in r.get("interests", [])]
                    return len(set(interests_list).intersection(set(r_interests)))
                
                # Filter by budget
                matched = [r for r in city_data["restaurants"] if r.get("budget") == budget_val]
                # Sort matched by interest score descending
                matched.sort(key=score_interest, reverse=True)
                
                # Pad with other budgets from same city if needed, sorted by interest match
                if len(matched) < 3:
                    others = [r for r in city_data["restaurants"] if r.get("budget") != budget_val]
                    others.sort(key=score_interest, reverse=True)
                    matched = (matched + others)[:3]
                else:
                    matched = matched[:3]
                
                # Format to expected markdown output
                lines = []
                for rest in matched:
                    lines.append(f"* **{rest['name']}**: {rest['price']}")
                    lines.append(f"\t+ {rest['cuisine']} cuisine")
                    lines.append(f"\t+ Must-try dishes: {rest['must_try']}")
                    if "description" in rest:
                        lines.append(f"\t+ {rest['description']}")
                return "\n".join(lines)
        except Exception as e:
            print(f"Error loading local restaurant database: {e}")
            
    # Fallback to LLM specific prompt if city not found in local db or database error
    try:
        interests_str = ", ".join(interests_list) if interests_list else "general dining"
        prompt = (
            f"Generate a list of 2-3 realistic restaurant recommendations in {city.title()} matching a {budget_val} budget level "
            f"and catering to {interests_str} interests.\n"
            "Format the output strictly as a markdown list with bold names, typical cost, cuisine, and a must-try dish.\n"
            "Do not include any greeting, introduction, or general trip advice. Return only the markdown list."
        )
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in restaurant_agent fallback: {e}")
        return f"Currently, I cannot fetch restaurant recommendations for {city}."