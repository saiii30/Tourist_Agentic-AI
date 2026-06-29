import os
import json
from rag_service import client

def restaurant_agent(question, city="None", interests="None", budget="None"):
    if city == "None":
        return "I need to know which city you are visiting to suggest restaurants."
        
    # Fallback to get_answer for restaurant recommendations
    print("Using RAG service for restaurant recommendations.")
    try:
        from rag_service import get_answer
        ans = get_answer(question)
        return ans.get("answer") if isinstance(ans, dict) else ans
    except Exception as e:
        print(f"Error in restaurant_agent fallback: {e}")
        return f"Currently, I cannot fetch restaurant recommendations for {city}."