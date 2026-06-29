import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph import graph
from supervisor import clear_guided_state, get_guided_state

def test_guided_flow():
    # Clear active states in SQLite
    print("Clearing guided state...")
    clear_guided_state()
    
    # Define conversational turns
    turns = [
        "plan a trip to goa",
        "next saturday",
        "2",
        "below 5000",
        "2",
        "friends",
        "nature"
    ]
    
    print("\n--- Starting Conversational Flow ---")
    for idx, turn in enumerate(turns, 1):
        print(f"\n[Turn {idx}] User: {turn}")
        
        result = graph.invoke(
            {
                "question": turn,
                "responses": [],
                "city": "None",
                "days": 3,
                "budget": "None",
                "travelers": 1,
                "travel_style": "None",
                "interests": "None"
            }
        )
        
        print(f"Bot Response:\n{result['answer']}")
        print(f"Routes: {result.get('routes', [])}")
        
        g_state = get_guided_state()
        print(f"Active DB State: {g_state}")

if __name__ == "__main__":
    test_guided_flow()
