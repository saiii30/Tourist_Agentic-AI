import os
import json
from rag_service import client

def nearby_agent(question, city="None", interests="None"):
    if city == "None":
        return "I need to know which city you are visiting to suggest nearby places."
        
    # Fallback to get_answer for nearby place recommendations
    print("Using RAG service for nearby place recommendations.")
    try:
        from rag_service import get_answer
        ans = get_answer(question)
        return ans.get("answer") if isinstance(ans, dict) else ans
    except Exception as e:
        print(f"Error in nearby_agent fallback: {e}")
        return f"Currently, I cannot fetch sightseeing suggestions for {city}."