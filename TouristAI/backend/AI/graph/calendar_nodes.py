import sys
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

# Adjust path to import correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.itinerary import Trip, ItineraryItem
from services.calendar_service import CalendarService
from services.itinerary_service import ItineraryService
from supervisor import get_guided_state, update_guided_state, clear_guided_state

calendar_service = CalendarService()
itinerary_service = ItineraryService()

def calendar_preview_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Renders the itinerary preview and asks the user for the next action.
    """
    g_state = get_guided_state()
    trip_id = g_state.get("trip_id")
    if not trip_id:
        trip_id = str(uuid.uuid4())
        update_guided_state("trip_id", trip_id)

    # Get itinerary from SQLite guided state cache
    cached_items_json = g_state.get("last_itinerary_items")
    items = []
    if cached_items_json:
        import json
        try:
            raw_items = json.loads(cached_items_json)
            items = [ItineraryItem(**item) for item in raw_items]
        except Exception as e:
            print(f"Error loading cached itinerary items: {e}")

    # Fallback to DB if SQLite cache is empty
    if not items and trip_id:
        items = calendar_service.repo.get_itinerary_items(trip_id)

    if items:
        # Render markdown from structured items to ensure consistency
        itinerary_md = calendar_service.render_itinerary_to_markdown(items)
    else:
        itinerary_md = g_state.get("last_itinerary", "")

    # Clean up markdown output
    preview_message = itinerary_md

    update_guided_state("last_itinerary", itinerary_md)
    update_guided_state("trip_status", "preview")

    return {
        "answer": preview_message,
        "responses": [f"Calendar:\n{itinerary_md}"],
        "routes": [],
        "transport_data": state.get("transport_data"),
        "transport_status": state.get("transport_status")
    }

def modify_itinerary_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Modifies specific activities in the itinerary based on natural language instructions.
    """
    if state["question"].strip().lower() in ["2", "modify", "modify itinerary"]:
        return {
            "answer": "What would you like to modify in your itinerary? Please specify the change (e.g., *'Replace Charminar with Golconda Fort'*, or *'Add shopping on day 1'*).",
            "responses": [],
            "routes": []
        }

    g_state = get_guided_state()
    trip_id = g_state.get("trip_id")
    
    if not trip_id:
        trip_id = str(uuid.uuid4())
        update_guided_state("trip_id", trip_id)

    # Read from SQLite guided state cache
    cached_items_json = g_state.get("last_itinerary_items")
    items = []
    if cached_items_json:
        import json
        try:
            raw_items = json.loads(cached_items_json)
            items = [ItineraryItem(**item) for item in raw_items]
        except Exception as e:
            print(f"Error loading cached itinerary items: {e}")

    # Fallback to DB
    if not items and trip_id:
        items = calendar_service.repo.get_itinerary_items(trip_id)

    # Perform natural language modification
    modified_items = itinerary_service.modify_itinerary(items, state["question"])
    
    # Re-geocode and recalculate OSRM routing on modified items
    from services.osrm_service import geocode_place, get_osrm_route
    
    city = g_state.get("destination", state.get("city", "None"))
    city_lower = city.lower().strip()
    
    # Resolve coordinates
    hotel_item = next((item for item in modified_items if item.category.lower() == "hotel"), None)
    if hotel_item:
        hotel_lat = hotel_item.latitude
        hotel_lng = hotel_item.longitude
    else:
        # Fallback to geocoded hotel from initial state
        hotel_lat, hotel_lng = geocode_place("Hotel", city)

    for item in modified_items:
        lat_val = item.latitude
        lng_val = item.longitude
        is_hyderabad = ("hyderabad" in city_lower)
        
        needs_geocoding = (
            lat_val is None or 
            lng_val is None or 
            (not is_hyderabad and lat_val is not None and abs(lat_val - 17.38) < 0.2)
        )
        
        if needs_geocoding and item.category.lower() not in ("transit", "transport"):
            plat, plng = geocode_place(item.activity or item.location, city)
            item.latitude = plat
            item.longitude = plng

    # Recalculate sequential travel times and OSRM routes day-by-day
    from collections import defaultdict
    day_groups = defaultdict(list)
    for item in modified_items:
        day_groups[item.day].append(item)
        
    for day, day_items in day_groups.items():
        # Sort day items by start_time
        day_items.sort(key=lambda x: x.start_time)
        
        current_lat = hotel_lat
        current_lng = hotel_lng
        
        for item in day_items:
            if item.category.lower() in ("transit", "transport"):
                continue
                
            lat = item.latitude
            lng = item.longitude
            
            dist = 0.0
            trav_mins = 0.0
            
            if current_lat is not None and current_lng is not None and lat is not None and lng is not None:
                dist, trav_mins = get_osrm_route(current_lat, current_lng, lat, lng)
                
            if dist == 0.0:
                item.travel_time = "0 mins"
                item.transport = "Stay"
                item.distance = "0 km"
            else:
                if trav_mins < 1.0:
                    item.travel_time = "1 min"
                else:
                    item.travel_time = f"{int(round(trav_mins))} mins"
                    
                if dist <= 1.0:
                    item.transport = "Walking"
                elif dist <= 5.0:
                    item.transport = "Auto Rickshaw"
                else:
                    item.transport = "Cab"
                item.distance = f"{dist:.1f} km"
                
            if lat is not None and lng is not None:
                current_lat = lat
                current_lng = lng

    # Convert modified items back to dicts and save to SQLite guided state cache
    modified_dicts = [item.dict() for item in modified_items]
    import json
    update_guided_state("last_itinerary_items", json.dumps(modified_dicts))

    # If the trip was already saved in PostgreSQL, update it there too
    if trip_id and calendar_service.repo.get_itinerary_items(trip_id):
        trip = Trip(
            trip_id=trip_id,
            user_id="guest_user",
            city=g_state.get("destination", state.get("city", "None")),
            days=int(g_state.get("days", state.get("days", 3))),
            budget=g_state.get("budget", state.get("budget", "Low")),
            travel_style=g_state.get("travel_style", state.get("travel_style", "Solo")),
            travelers=int(g_state.get("travelers", state.get("travelers", 1))),
            interests=g_state.get("interests", state.get("interests", "None")),
            status="saved",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        calendar_service.save_itinerary(trip, modified_items)

    # Render modified itinerary back to markdown and preview it
    itinerary_md = calendar_service.render_itinerary_to_markdown(modified_items)
    update_guided_state("last_itinerary", itinerary_md)

    # If the trip was already synced to Google Calendar, trigger an update to only affected events
    if trip_id and calendar_service.gcal_service.is_authenticated():
        calendar_events = calendar_service.repo.get_calendar_events(trip_id)
        if calendar_events:
            # Re-sync to Google Calendar (this will automatically update existing events and delete obsolete ones)
            travel_date = g_state.get("travel_date", "None")
            calendar_service.sync_to_google_calendar(trip_id, start_date_str=travel_date)

    return calendar_preview_node(state)

def save_itinerary_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Saves the itinerary to the SQLite database without prompting for Google Calendar sync.
    """
    g_state = get_guided_state()
    trip_id = g_state.get("trip_id")
    
    if not trip_id:
        trip_id = str(uuid.uuid4())
        update_guided_state("trip_id", trip_id)

    items = calendar_service.repo.get_itinerary_items(trip_id)
    if not items:
        cached_items_json = g_state.get("last_itinerary_items")
        if cached_items_json:
            import json
            try:
                raw_items = json.loads(cached_items_json)
                items = [ItineraryItem(**item) for item in raw_items]
            except Exception as e:
                print(f"Error loading cached itinerary items: {e}")
                items = []
        else:
            items = []

    city = g_state.get("destination", state.get("city", "None"))
    trip = Trip(
        trip_id=trip_id,
        user_id="guest_user",
        city=city,
        days=int(g_state.get("days", state.get("days", 3))),
        budget=g_state.get("budget", state.get("budget", "Low")),
        travel_style=g_state.get("travel_style", state.get("travel_style", "Solo")),
        travelers=int(g_state.get("travelers", state.get("travelers", 1))),
        interests=g_state.get("interests", state.get("interests", "None")),
        status="saved",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    calendar_service.save_itinerary(trip, items)
    
    # Save confirmation - skip calendar sync prompt
    update_guided_state("trip_status", "completed")

    msg = (
        f"✅ **Itinerary Saved Successfully!**\n\n"
        f"I have saved the structured itinerary for your trip to **{city.title()}** in the local database.\n\n"
        "You can use the 'Save Trip' button in the UI to sync with Google Calendar when needed."
    )

    return {
        "answer": msg,
        "responses": [],
        "routes": []
    }

def google_calendar_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Syncs the saved itinerary with Google Calendar, handling OAuth redirect if needed.
    """
    g_state = get_guided_state()
    trip_id = g_state.get("trip_id")
    
    if not g_state.get("travel_date") or g_state.get("travel_date") == "None":
        travel_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        travel_date = g_state.get("travel_date")

    # If the user replies "no" to calendar integration
    question_lower = state["question"].strip().lower()
    if question_lower in ["no", "nope", "don't", "cancel", "nay"]:
        update_guided_state("trip_status", "completed")
        return {
            "answer": "No problem! Your itinerary is saved in the local database. Have a safe trip!",
            "responses": [],
            "routes": []
        }

    # Call calendar service sync
    res = calendar_service.sync_to_google_calendar(trip_id, start_date_str=travel_date)
    
    if not res.get("success") and res.get("needs_auth"):
        # We need authentication - show login URL
        auth_url = res.get("auth_url")
        msg = (
            "🔗 **Google Calendar Integration**\n\n"
            "Please click the link below to authorize access to your Google Calendar:\n\n"
            f"[👉 **Authorize Google Calendar Access**]({auth_url})\n\n"
            "Once you authorize, close the tab and return here. Your calendar events will be created automatically!"
        )
        return {
            "answer": msg,
            "google_auth_url": auth_url,
            "responses": [],
            "routes": []
        }
    
    # Successful sync
    update_guided_state("trip_status", "completed")
    success_msg = (
        "📅 **Google Calendar Sync Successful!**\n\n"
        "I have added all activities of your trip to your primary Google Calendar! "
        "A default reminder has been set for **30 minutes before** each activity."
    )
    return {
        "answer": success_msg,
        "responses": [],
        "routes": []
    }

def regenerate_itinerary_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sets up the state for programmatic regeneration using alternative agent data.
    """
    g_state = get_guided_state()
    # Increment regen count
    regen_count = int(g_state.get("regen_count", 0)) + 1
    update_guided_state("regen_count", str(regen_count))
    
    print(f"[INFO] Incrementing regeneration offset to: {regen_count}")
    
    return {
        "routes": ["hotel", "restaurant", "nearby", "weather"]
    }

def delete_itinerary_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deletes the current trip and its corresponding calendar events.
    """
    g_state = get_guided_state()
    trip_id = g_state.get("trip_id")
    
    if trip_id:
        calendar_service.delete_trip_and_calendar(trip_id)
        
    clear_guided_state()
    
    msg = (
        "🗑️ **Itinerary Deleted Successfully**\n\n"
        "Your trip record has been removed from SQLite, and all corresponding "
        "Google Calendar events have been deleted. Let me know if you want to plan another trip!"
    )
    
    return {
        "answer": msg,
        "responses": [],
        "routes": []
    }
