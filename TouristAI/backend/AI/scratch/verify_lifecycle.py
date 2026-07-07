import sys
import os
import uuid
import sqlite3
import io
from datetime import datetime

# Set stdout to use UTF-8 to prevent encoding errors on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Adjust path to import correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.sqlite import SQLiteDatabase
from models.itinerary import Trip, ItineraryItem
from repositories.trip_repository import TripRepository
from services.itinerary_service import ItineraryService
from services.calendar_service import CalendarService
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "graph"))
from calendar_nodes import (
    calendar_preview_node,
    modify_itinerary_node,
    save_itinerary_node,
    delete_itinerary_node,
    regenerate_itinerary_node
)
from supervisor import update_guided_state, clear_guided_state

def test_database_and_repository():
    print("--- 1. Testing Database and Repository CRUD ---")
    repo = TripRepository()
    
    trip_id = f"test-trip-{uuid.uuid4()}"
    trip = Trip(
        trip_id=trip_id,
        user_id="test_user",
        city="goa",
        days=2,
        budget="Budget",
        travel_style="Friends",
        travelers=2,
        interests="Nature",
        status="draft",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    # Test Create
    repo.create_trip(trip)
    fetched_trip = repo.get_trip(trip_id)
    assert fetched_trip is not None, "Failed to retrieve trip"
    assert fetched_trip.city == "goa", "Incorrect city name in trip"
    print(" [✓] Trip creation and retrieval verified")

    # Test Status Update
    repo.update_trip_status(trip_id, "saved")
    updated_trip = repo.get_trip(trip_id)
    assert updated_trip.status == "saved", "Failed to update trip status"
    print(" [✓] Trip status update verified")

    # Test Save Itinerary Items
    items = [
        ItineraryItem(
            day=1,
            start_time="09:00",
            end_time="12:00",
            activity="Visit Arambol Beach",
            location="Arambol Beach",
            category="Sightseeing",
            notes="Enjoy sunset drum circle"
        ),
        ItineraryItem(
            day=2,
            start_time="13:00",
            end_time="14:30",
            activity="Lunch at Brittos",
            location="Baga Beach",
            category="Food",
            restaurant="Britto's Restaurant",
            notes="Try chicken xacuti"
        )
    ]
    repo.save_itinerary_items(trip_id, items)
    fetched_items = repo.get_itinerary_items(trip_id)
    assert len(fetched_items) == 2, f"Expected 2 items, got {len(fetched_items)}"
    assert fetched_items[0].activity == "Visit Arambol Beach", "Incorrect activity details"
    print(" [✓] Itinerary item saving and retrieval verified")

    # Test Calendar Event Mapping
    google_event_id = "mock-google-event-xyz"
    repo.save_calendar_event(trip_id, 1, "Visit Arambol Beach", google_event_id, "primary")
    events = repo.get_calendar_events(trip_id)
    assert len(events) == 1, "Failed to save calendar event mapping"
    assert events[0]["google_event_id"] == google_event_id, "Incorrect mapped Google Event ID"
    print(" [✓] Google Calendar event mapping verified")

    # Test Delete
    repo.delete_trip(trip_id)
    assert repo.get_trip(trip_id) is None, "Trip was not deleted"
    assert len(repo.get_itinerary_items(trip_id)) == 0, "Associated itineraries were not cascade deleted"
    assert len(repo.get_calendar_events(trip_id)) == 0, "Associated calendar mappings were not cascade deleted"
    print(" [✓] Trip and associated cascade deletions verified")

def test_itinerary_parsing_and_modification():
    print("\n--- 2. Testing Itinerary Parsing and Modification Services ---")
    it_service = ItineraryService()
    
    # Test Parsing Markdown
    markdown = """
# Day 1
🏨 Hotel:
Treebo Select Vagator

🍳 Breakfast:
Breakfast at hotel

🌅 Morning (09:00–12:00)
Visit Arambol Beach. Beautiful bohemian beach.

🍽 Lunch
Lunch at Britto's.

🌇 Afternoon (02:00–05:00)
Explore Basilica of Bom Jesus. Historical church.
"""
    items = it_service.parse_markdown_to_items(markdown)
    assert len(items) > 0, "Failed to parse markdown itinerary to structured list"
    assert items[0].day == 1, "Incorrect parsed day"
    print(f" [✓] Parsed markdown into {len(items)} structured events successfully:")
    for i, it in enumerate(items, 1):
        print(f"     {i}. Day {it.day} | {it.start_time}-{it.end_time} | {it.activity} at {it.location}")

    # Test Modification Logic
    print(" Running LLM natural language edit: 'Replace Arambol Beach with Mandovi River Cruise'")
    modified = it_service.modify_itinerary(items, "Replace Arambol Beach with Mandovi River Cruise")
    assert len(modified) > 0, "Failed to modify itinerary"
    
    has_cruise = any("Mandovi River" in it.activity or "Cruise" in it.activity for it in modified)
    assert has_cruise, "Modification request was not executed in the structured items"
    print(" [✓] Natural language itinerary modifications verified successfully:")
    for i, it in enumerate(modified, 1):
        print(f"     {i}. Day {it.day} | {it.start_time}-{it.end_time} | {it.activity} at {it.location}")

def test_langgraph_nodes():
    print("\n--- 3. Testing LangGraph State Transitions and Flow ---")
    clear_guided_state()
    
    trip_id = f"test-flow-{uuid.uuid4()}"
    update_guided_state("trip_id", trip_id)
    update_guided_state("destination", "Goa")
    update_guided_state("days", "2")
    update_guided_state("budget", "Budget")
    update_guided_state("travel_style", "Solo")
    update_guided_state("travelers", "1")
    update_guided_state("interests", "Nature")
    
    # Mock last itinerary
    last_itinerary_md = """# Day 1
🏨 Hotel: Treebo Select Vagator
🍳 Breakfast: Breakfast at hotel
🌅 Morning (09:00–12:00)
**Visit Arambol Beach** at Arambol. Enjoy bohemian vibe.
🍽 Lunch
Lunch at Britto's.
🌇 Afternoon (02:00–05:00)
Explore Basilica of Bom Jesus.
"""
    update_guided_state("last_itinerary", last_itinerary_md)
    
    # Test Preview Node
    state = {
        "question": "what next?",
        "routes": [],
        "responses": [],
        "answer": "",
        "city": "Goa",
        "days": 2,
        "budget": "Budget",
        "travelers": 1,
        "travel_style": "Solo",
        "interests": "Nature"
    }
    
    res_preview = calendar_preview_node(state)
    assert "What would you like to do next?" in res_preview["answer"], "Preview node did not offer options"
    print(" [✓] Calendar Preview node generated options successfully")

    # Test Save Node
    res_save = save_itinerary_node(state)
    assert "Saved Successfully" in res_save["answer"], "Save node failed to confirm save"
    print(" [✓] Calendar Save node saved trip successfully")

    # Test Delete Node
    res_delete = delete_itinerary_node(state)
    assert "Deleted Successfully" in res_delete["answer"], "Delete node failed to confirm deletion"
    print(" [✓] Calendar Delete node deleted trip successfully")

if __name__ == "__main__":
    try:
        test_database_and_repository()
        test_itinerary_parsing_and_modification()
        test_langgraph_nodes()
        print("\nAll lifecycle verification checks passed successfully!")
    except AssertionError as ae:
        print(f"\nAssertion error during verification: {ae}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during verification: {e}")
        sys.exit(1)
