import os
import sys
import sqlite3

# Add AI folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import graph
from supervisor import clear_guided_state, get_db_path, get_guided_state

def test_conversational_save():
    print("1. Cleaning database table 'calendar_events'...")
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM calendar_events")
    conn.commit()
    conn.close()

    clear_guided_state()
    
    # 2. Complete planning turns to generate an itinerary
    turns = [
        "plan a trip to goa",
        "next saturday",
        "2",
        "below 5000",
        "2",
        "friends",
        "nature"
    ]
    
    print("\n2. Simulating planning flow...")
    result = None
    for turn in turns:
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
        
    print(f"\nFinal synthesized bot response ends with:")
    lines = result['answer'].split('\n')
    print("\n".join(lines[-4:]))
    
    # Check that confirmation flag is set to 1
    g_state = get_guided_state()
    print(f"\nFlag 'awaiting_save_confirmation': {g_state.get('awaiting_save_confirmation')}")
    print(f"Cached 'last_itinerary' exists: {bool(g_state.get('last_itinerary'))}")

    # 3. Send "yes" to confirm saving
    print("\n3. Sending confirmation: 'yes, save it please'")
    res_confirm = graph.invoke(
        {
            "question": "yes, save it please",
            "responses": [],
            "city": "None",
            "days": 3,
            "budget": "None",
            "travelers": 1,
            "travel_style": "None",
            "interests": "None"
        }
    )
    print(f"\nBot Response to 'yes':")
    print(res_confirm['answer'])

    # 4. Verify calendar_events is populated
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT trip_name, day_num, time_slot, activity FROM calendar_events ORDER BY day_num, id")
    events = c.fetchall()
    conn.close()
    
    print(f"\n4. Saved Events in SQLite 'calendar_events':")
    if events:
        for idx, ev in enumerate(events, 1):
            print(f" [{idx}] Trip: {ev[0]} | Day {ev[1]} | Slot: {ev[2]} | Activity: {ev[3]}")
        print("\nSUCCESS: Events are saved correctly!")
    else:
        print("\nFAILURE: No events found in SQLite!")

if __name__ == "__main__":
    test_conversational_save()
