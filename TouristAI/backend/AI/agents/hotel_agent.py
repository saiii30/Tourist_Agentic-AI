import os
import json
from rag_service import client

def hotel_agent(question, city="None", budget="None", travelers=1):
    if city == "None":
        return "I need to know which city you are visiting to suggest hotels."
        
    # Fallback to get_answer for hotel recommendations
    print("Using RAG service for hotel recommendations.")
    try:
        from rag_service import get_answer
        ans = get_answer(question)
        return ans.get("answer") if isinstance(ans, dict) else ans
    except Exception as e:
        print(f"Error in hotel_agent fallback: {e}")
        return f"Currently, I cannot fetch hotel recommendations for {city}."