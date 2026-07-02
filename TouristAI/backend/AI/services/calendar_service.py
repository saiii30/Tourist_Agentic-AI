import sys
import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Adjust path to import correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.itinerary import ItineraryItem, Trip
from repositories.trip_repository import TripRepository
from services.google_calendar_service import GoogleCalendarService

logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self, user_id: str = "guest_user") -> None:
        self.user_id = user_id
        self.repo = TripRepository()
        self.gcal_service = GoogleCalendarService(user_id=user_id)

    def save_itinerary(self, trip: Trip, items: List[ItineraryItem]) -> None:
        """
        Saves a trip and its itinerary activities to SQLite.
        """
        # Save trip details
        self.repo.create_trip(trip)
        # Link items to trip_id
        for item in items:
            item.trip_id = trip.trip_id
        self.repo.save_itinerary_items(trip.trip_id, items)

    def sync_to_google_calendar(self, trip_id: str, start_date_str: str, reminder_minutes: int = 30) -> Dict[str, Any]:
        """
        Syncs trip activities to Google Calendar. Supports creation and partial updates.
        """
        # If credentials are not configured, perform a mock sync to simulate success in local DB
        if not self.gcal_service.is_configured():
            logger.warning("Google Calendar API credentials are not configured. Running in simulated Google Calendar Sync mode.")
            trip = self.repo.get_trip(trip_id)
            if not trip:
                # If trip not found in repository, create a draft one using guided state
                from supervisor import get_guided_state
                g_state = get_guided_state()
                city = g_state.get("destination", "Unknown")
                days = int(g_state.get("days", 3))
                budget = g_state.get("budget", "Moderate")
                travel_style = g_state.get("travel_style", "Solo")
                travelers = int(g_state.get("travelers", 1))
                interests = g_state.get("interests", "None")
                
                trip = Trip(
                    trip_id=trip_id,
                    user_id=self.user_id,
                    city=city,
                    days=days,
                    budget=budget,
                    travel_style=travel_style,
                    travelers=travelers,
                    interests=interests,
                    status="draft",
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                
                # Fetch calendar items from state to save
                cached_items_json = g_state.get("last_itinerary_items")
                if cached_items_json:
                    import json
                    try:
                        raw_items = json.loads(cached_items_json)
                        parsed_items = [ItineraryItem(**item) for item in raw_items]
                        self.save_itinerary(trip, parsed_items)
                    except Exception as e:
                        logger.error(f"Error parsing cached items during mock sync: {e}")
            
            # Now fetch items again
            items = self.repo.get_itinerary_items(trip_id)
            if not items:
                return {"success": False, "message": "No itinerary items found to sync (Simulated Mode)"}
                
            # Create simulated calendar event mappings
            # First, clean existing mappings to avoid duplicates
            existing = self.repo.get_calendar_events(trip_id)
            existing_event_ids = [m["google_event_id"] for m in existing]
            for event_id in existing_event_ids:
                self.repo.delete_calendar_event(trip_id, event_id)
                
            for item in items:
                simulated_event_id = f"simulated-gcal-event-{uuid.uuid4()}"
                self.repo.save_calendar_event(trip_id, item.day, item.activity, simulated_event_id, "primary")
                
            self.repo.update_trip_status(trip_id, "synced")
            return {
                "success": True,
                "message": f"Successfully synced {len(items)} events to Google Calendar (Simulated Mode)."
            }

        if not self.gcal_service.is_authenticated():
            return {
                "success": False,
                "needs_auth": True,
                "auth_url": self.gcal_service.get_authorization_url(trip_id)
            }

        trip = self.repo.get_trip(trip_id)
        if not trip:
            return {"success": False, "message": f"Trip {trip_id} not found"}

        items = self.repo.get_itinerary_items(trip_id)
        if not items:
            return {"success": False, "message": "No itinerary items to sync"}

        # Determine starting date
        try:
            start_date = datetime.strptime(start_date_str.strip(), "%Y-%m-%d")
        except ValueError:
            # Fallback parsing
            try:
                start_date = datetime.strptime(start_date_str.strip(), "%Y%m%d")
            except ValueError:
                start_date = datetime.now() + timedelta(days=1)

        # Get existing synced events mapping for this trip
        existing_mappings = self.repo.get_calendar_events(trip_id)
        # Create a lookup table for faster retrieval: (day, activity_name) -> google_event_id
        mappings_lookup = {
            (m["day"], m["activity"]): m["google_event_id"]
            for m in existing_mappings
        }

        # Keep track of active event IDs during this sync
        synced_event_ids = set()

        for item in items:
            # Construct Google Calendar Event body
            event_date = start_date + timedelta(days=(item.day - 1))
            
            try:
                sh, sm = map(int, item.start_time.split(":"))
            except ValueError:
                sh, sm = 9, 0
            try:
                eh, em = map(int, item.end_time.split(":"))
            except ValueError:
                eh, em = 12, 0

            start_dt = datetime(event_date.year, event_date.month, event_date.day, sh, sm)
            end_dt = datetime(event_date.year, event_date.month, event_date.day, eh, em)

            description = f"{item.notes or ''}"
            if item.restaurant:
                description += f"\nRecommended Restaurant: {item.restaurant}"
            if item.hotel:
                description += f"\nStaying at: {item.hotel}"

            event_body = {
                'summary': item.activity,
                'location': item.location,
                'description': description,
                'start': {
                    'dateTime': start_dt.isoformat() + "+05:30",
                    'timeZone': 'Asia/Kolkata',
                },
                'end': {
                    'dateTime': end_dt.isoformat() + "+05:30",
                    'timeZone': 'Asia/Kolkata',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': reminder_minutes},
                    ],
                },
            }

            lookup_key = (item.day, item.activity)
            if lookup_key in mappings_lookup:
                # Event already exists -> Update it (Affected parts only)
                g_event_id = mappings_lookup[lookup_key]
                try:
                    self.gcal_service.update_event(g_event_id, event_body)
                    synced_event_ids.add(g_event_id)
                except Exception as e:
                    logger.error(f"Error updating Google event {g_event_id}: {e}")
                    # Recreate if it was deleted on Google Calendar
                    new_id = self.gcal_service.create_event(event_body)
                    self.repo.save_calendar_event(trip_id, item.day, item.activity, new_id, "primary")
                    synced_event_ids.add(new_id)
            else:
                # Event does not exist -> Create new
                try:
                    new_id = self.gcal_service.create_event(event_body)
                    self.repo.save_calendar_event(trip_id, item.day, item.activity, new_id, "primary")
                    synced_event_ids.add(new_id)
                except Exception as e:
                    logger.error(f"Error creating Google Calendar event: {e}")
                    return {"success": False, "message": f"Google Calendar API Error: {str(e)}"}

        # Delete any Google Calendar events that were in mapping but no longer exist in the new itinerary
        for m in existing_mappings:
            if m["google_event_id"] not in synced_event_ids:
                try:
                    self.gcal_service.delete_event(m["google_event_id"])
                    self.repo.delete_calendar_event(trip_id, m["google_event_id"])
                except Exception as e:
                    logger.error(f"Error deleting obsolete Google event {m['google_event_id']}: {e}")

        # Update trip status in SQLite
        self.repo.update_trip_status(trip_id, "synced")
        
        return {
            "success": True,
            "message": f"Successfully synced {len(items)} events to Google Calendar."
        }

    def delete_trip_and_calendar(self, trip_id: str) -> None:
        """
        Deletes a trip from database and cancels all corresponding Google Calendar events.
        """
        mappings = self.repo.get_calendar_events(trip_id)
        if self.gcal_service.is_authenticated():
            for m in mappings:
                try:
                    self.gcal_service.delete_event(m["google_event_id"])
                except Exception as e:
                    logger.error(f"Error deleting event {m['google_event_id']} during trip deletion: {e}")

        # Delete SQLite records (CASCADE will handle itineraries and calendar_events)
        self.repo.delete_trip(trip_id)

    @staticmethod
    def render_itinerary_to_markdown(items: List[ItineraryItem]) -> str:
        """
        Formats a structured ItineraryItem list back to a beautiful, clean Markdown.
        """
        sorted_items = sorted(items, key=lambda x: (x.day, x.start_time))
        days_dict = {}
        for item in sorted_items:
            if item.day not in days_dict:
                days_dict[item.day] = []
            days_dict[item.day].append(item)

        lines = []
        hotels = [item.hotel for item in sorted_items if item.hotel]
        hotel_name = hotels[0] if hotels else "Local Hotel"

        for day in sorted(days_dict.keys()):
            day_items = days_dict[day]
            lines.append(f"# Day {day}\n")
            lines.append(f"🏨 Hotel:\n{hotel_name}\n")
            
            # Breakfast
            breakfast_item = None
            for item in day_items:
                if "breakfast" in item.activity.lower() or (item.category == "Food" and item.start_time < "10:00"):
                    breakfast_item = item
                    break
            
            if breakfast_item:
                lines.append(f"🍳 Breakfast:\n{breakfast_item.activity} at {breakfast_item.location}. {breakfast_item.notes or ''}\n")
            else:
                lines.append("🍳 Breakfast:\nBreakfast at the hotel or nearby cafe.\n")

            # Morning (09:00 - 12:00)
            morning_items = [item for item in day_items if item.start_time >= "09:00" and item.end_time <= "13:00" and item != breakfast_item]
            lines.append("🌅 Morning (09:00–12:00)")
            if morning_items:
                for item in morning_items:
                    lines.append(f"- **{item.activity}** at {item.location}. {item.notes or ''}")
            else:
                lines.append("- Explore local sightseeing viewpoints and temples.")
            lines.append("")

            # Lunch
            lunch_item = None
            for item in day_items:
                if "lunch" in item.activity.lower() or (item.category == "Food" and "12:00" <= item.start_time <= "15:00" and item != breakfast_item):
                    lunch_item = item
                    break
            if lunch_item:
                lines.append(f"🍽 Lunch\n{lunch_item.activity} at {lunch_item.location}. {lunch_item.notes or ''}\n")
            else:
                lines.append("🍽 Lunch\nEnjoy delicious local cuisine at a recommended eatery.\n")

            # Afternoon (02:00 - 05:00)
            afternoon_items = [item for item in day_items if item.start_time >= "13:00" and item.end_time <= "18:00" and item != lunch_item]
            lines.append("🌇 Afternoon (02:00–05:00)")
            if afternoon_items:
                for item in afternoon_items:
                    lines.append(f"- **{item.activity}** at {item.location}. {item.notes or ''}")
            else:
                lines.append("- Relax and stroll in the nearby shopping bazaar.")
            lines.append("")

            # Evening
            evening_items = [item for item in day_items if item.start_time >= "17:00" and item.end_time <= "20:30" and item.category != "Food" and item not in morning_items and item not in afternoon_items]
            lines.append("🌙 Evening")
            if evening_items:
                for item in evening_items:
                    lines.append(f"- **{item.activity}** at {item.location}. {item.notes or ''}")
            else:
                lines.append("- Relax at local viewpoints or check out cultural shows.")
            lines.append("")

            # Dinner
            dinner_item = None
            for item in day_items:
                if "dinner" in item.activity.lower() or (item.category == "Food" and item.start_time >= "18:30" and item != lunch_item and item != breakfast_item):
                    dinner_item = item
                    break
            if dinner_item:
                lines.append(f"🍴 Dinner\nHave dinner at **{dinner_item.activity}** ({dinner_item.location}). Try the recommended must-try items: *{dinner_item.notes or ''}*.\n")
            else:
                lines.append("🍴 Dinner\nDine at a local restaurant for a cozy dinner.\n")

            # Cost
            # Estimate roughly
            lines.append("💰 Estimated Daily Cost\n₹2,500 - ₹3,500\n")
            lines.append("---")

        return "\n".join(lines)
