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

    # Get itinerary from database or from last_itinerary
    last_itinerary = g_state.get("last_itinerary", "")
    items = calendar_service.repo.get_itinerary_items(trip_id)
    
    if items:
        # Render markdown from structured items to ensure consistency
        itinerary_md = calendar_service.render_itinerary_to_markdown(items)
    else:
        itinerary_md = last_itinerary
        # Parse it now to cache structured records in database
        if itinerary_md:
            parsed_items = []
            cached_items_json = g_state.get("last_itinerary_items")
            if cached_items_json:
                import json
                try:
                    raw_items = json.loads(cached_items_json)
                    parsed_items = [ItineraryItem(**item) for item in raw_items]
                except Exception as e:
                    print(f"Error loading cached itinerary items: {e}")
                    
            if parsed_items:
                trip = Trip(
                    trip_id=trip_id,
                    user_id="guest_user",
                    city=g_state.get("destination", state.get("city", "None")),
                    days=int(g_state.get("days", state.get("days", 3))),
                    budget=g_state.get("budget", state.get("budget", "Budget")),
                    travel_style=g_state.get("travel_style", state.get("travel_style", "Solo")),
                    travelers=int(g_state.get("travelers", state.get("travelers", 1))),
                    interests=g_state.get("interests", state.get("interests", "None")),
                    status="draft",
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                calendar_service.save_itinerary(trip, parsed_items)

    # Clean up markdown output
    preview_message = (
        f"{itinerary_md}\n\n"
        "**What would you like to do next?**\n\n"
        "1. **Save Itinerary**\n"
        "2. **Modify Itinerary** (e.g. *'Replace Boat House with Avalanche Lake'*, *'Add shopping in evening'*)\n"
        "3. **Regenerate Itinerary**"
    )

    update_guided_state("last_itinerary", itinerary_md)
    update_guided_state("awaiting_preview_action", "1")

    return {
        "answer": preview_message,
        "responses": [f"Calendar:\n{itinerary_md}"],
        "routes": []
    }

def modify_itinerary_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Modifies specific activities in the itinerary based on natural language instructions.
    """
    g_state = get_guided_state()
    trip_id = g_state.get("trip_id")
    
    if not trip_id:
        trip_id = str(uuid.uuid4())
        update_guided_state("trip_id", trip_id)

    items = calendar_service.repo.get_itinerary_items(trip_id)
    if not items:
        # Fallback to parsing from cached items
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

    # Perform natural language modification
    modified_items = itinerary_service.modify_itinerary(items, state["question"])
    
    # Save modified items
    trip = Trip(
        trip_id=trip_id,
        user_id="guest_user",
        city=g_state.get("destination", state.get("city", "None")),
        days=int(g_state.get("days", state.get("days", 3))),
        budget=g_state.get("budget", state.get("budget", "Budget")),
        travel_style=g_state.get("travel_style", state.get("travel_style", "Solo")),
        travelers=int(g_state.get("travelers", state.get("travelers", 1))),
        interests=g_state.get("interests", state.get("interests", "None")),
        status="draft",
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
    Saves the itinerary to the SQLite database and prompts for Google Calendar sync.
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
        budget=g_state.get("budget", state.get("budget", "Budget")),
        travel_style=g_state.get("travel_style", state.get("travel_style", "Solo")),
        travelers=int(g_state.get("travelers", state.get("travelers", 1))),
        interests=g_state.get("interests", state.get("interests", "None")),
        status="saved",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    calendar_service.save_itinerary(trip, items)
    
    # Save confirmation
    update_guided_state("awaiting_preview_action", "0")
    update_guided_state("awaiting_google_sync", "1")

    msg = (
        f"✅ **Itinerary Saved Successfully!**\n\n"
        f"I have saved the structured itinerary for your trip to **{city.title()}** in the local database.\n\n"
        "Would you like to add this itinerary to your **Google Calendar**? (Yes/No)"
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
        update_guided_state("awaiting_google_sync", "0")
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
    update_guided_state("awaiting_google_sync", "0")
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
    Generates a completely different itinerary draft, avoiding repeating the previous one.
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

    trip = Trip(
        trip_id=trip_id,
        user_id="guest_user",
        city=g_state.get("destination", state.get("city", "None")),
        days=int(g_state.get("days", state.get("days", 3))),
        budget=g_state.get("budget", state.get("budget", "Budget")),
        travel_style=g_state.get("travel_style", state.get("travel_style", "Solo")),
        travelers=int(g_state.get("travelers", state.get("travelers", 1))),
        interests=g_state.get("interests", state.get("interests", "None")),
        status="draft",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )

    # Regenerate a different itinerary
    regenerated_items = itinerary_service.regenerate_itinerary(trip, items)
    calendar_service.save_itinerary(trip, regenerated_items)

    # Format new draft
    itinerary_md = calendar_service.render_itinerary_to_markdown(regenerated_items)
    update_guided_state("last_itinerary", itinerary_md)

    return calendar_preview_node(state)

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
