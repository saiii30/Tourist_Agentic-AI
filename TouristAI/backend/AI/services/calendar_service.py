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
        Syncs trip activities to Google Calendar. Supports creation, updates, and deletes.
        """
        trip = self.repo.get_trip(trip_id)
        if not trip:
            # Try to fetch/create a fallback trip using guided state
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
                status="GENERATED",
                travel_date=start_date_str,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            # Fetch calendar items from state to save
            cached_items_json = g_state.get("last_itinerary_items")
            if cached_items_json:
                import json
                try:
                    raw_items = json.loads(cached_items_json)
                    parsed_items = []
                    for item in raw_items:
                        parsed_items.append(ItineraryItem(
                            trip_id=trip_id,
                            day=item.get("day", 1),
                            start_time=item.get("start_time", "09:00"),
                            end_time=item.get("end_time", "12:00"),
                            activity=item.get("activity", "Activity"),
                            location=item.get("location", ""),
                            category=item.get("category", "Sightseeing"),
                            restaurant=item.get("restaurant"),
                            hotel=item.get("hotel"),
                            notes=item.get("notes"),
                            activity_id=item.get("activity_id") or str(uuid.uuid4()),
                            google_event_id=item.get("google_event_id")
                        ))
                    self.save_itinerary(trip, parsed_items)
                except Exception as e:
                    logger.error(f"Error parsing cached items during mock sync: {e}")

        # Update service with trip-specific user ID to prevent token collision
        user_id = trip.user_id if trip.user_id else self.user_id
        self.gcal_service = GoogleCalendarService(user_id=user_id)

        items = self.repo.get_itinerary_items(trip_id)
        if not items:
            return {"success": False, "message": "No itinerary items found to sync"}

        # Metrics for logs
        created_count = 0
        updated_count = 0
        deleted_count = 0

        # Determine starting date
        date_str = start_date_str.strip()
        start_date = None
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y", "%Y%m%d"):
            try:
                start_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
                
        if not start_date:
            # Try parsing natural language date using LLM helper
            parsed_str = self._parse_natural_date(date_str)
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y", "%Y%m%d"):
                try:
                    start_date = datetime.strptime(parsed_str.strip(), fmt)
                    break
                except ValueError:
                    continue
                    
        if not start_date:
            start_date = datetime.now() + timedelta(days=1)

        # 1. Simulated Mode (Credentials not configured)
        if not self.gcal_service.is_configured():
            logger.warning("Google Calendar API credentials are not configured. Running in simulated Google Calendar Sync mode.")
            # Clear existing calendar mappings to avoid duplicates
            existing = self.repo.get_calendar_events(trip_id)
            for m in existing:
                self.repo.delete_calendar_event(trip_id, m["google_event_id"])
                deleted_count += 1
                
            for item in items:
                if not item.google_event_id:
                    simulated_event_id = f"simulated-gcal-event-{uuid.uuid4()}"
                    self.repo.update_google_event_id(trip_id, item.activity_id, simulated_event_id)
                    item.google_event_id = simulated_event_id
                    created_count += 1
                else:
                    updated_count += 1
                
                # Keep calendar_events mapping table in sync
                self.repo.save_calendar_event(trip_id, item.day, item.activity, item.google_event_id, "primary")
                
            self.repo.update_trip_status(trip_id, "SYNCED")
            
            # Log Sync Success
            self.repo.log_sync_event({
                "trip_id": trip_id,
                "user_id": user_id,
                "status": "SYNCED",
                "events_created": created_count,
                "events_updated": updated_count,
                "events_deleted": deleted_count,
                "error": None
            })
            
            return {
                "success": True,
                "simulated": True,
                "message": f"Successfully synced {len(items)} events to Google Calendar (Simulated Mode)."
            }

        # 2. Check Authentication for Real OAuth Sync
        if not self.gcal_service.is_authenticated():
            return {
                "success": False,
                "needs_auth": True,
                "auth_url": self.gcal_service.get_authorization_url(trip_id)
            }

        # 3. Real OAuth Sync Mode
        try:
            # Fetch user primary calendar timezone dynamically
            try:
                gcal = self.gcal_service.get_calendar_service()
                calendar_meta = gcal.calendars().get(calendarId='primary').execute()
                user_timezone = calendar_meta.get('timeZone', 'Asia/Kolkata')
            except Exception as tz_ex:
                logger.warning(f"Could not retrieve user calendar timezone, defaulting to Asia/Kolkata: {tz_ex}")
                user_timezone = 'Asia/Kolkata'

            # Map current items by activity_id
            current_ids = {item.activity_id for item in items}
            
            # Find and delete events on Google Calendar that were previously synced but no longer exist locally
            existing_mappings = self.repo.get_calendar_events(trip_id)
            for m in existing_mappings:
                # Find if there is any local item with matching google_event_id
                matched_item = next((it for it in items if it.google_event_id == m["google_event_id"]), None)
                if not matched_item:
                    try:
                        self.gcal_service.delete_event(m["google_event_id"])
                    except Exception as e:
                        logger.error(f"Error deleting Google event {m['google_event_id']}: {e}")
                    self.repo.delete_calendar_event(trip_id, m["google_event_id"])
                    deleted_count += 1

            # Sync current items
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

                # Handle events crossing midnight or zero-duration events to avoid Google Calendar timeRangeEmpty errors
                if end_dt < start_dt:
                    end_dt += timedelta(days=1)
                elif end_dt == start_dt:
                    end_dt += timedelta(minutes=30)

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
                        'dateTime': start_dt.isoformat(),
                        'timeZone': user_timezone,
                    },
                    'end': {
                        'dateTime': end_dt.isoformat(),
                        'timeZone': user_timezone,
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'popup', 'minutes': reminder_minutes},
                        ],
                    },
                }

                # Check if it has a google_event_id already mapped
                g_event_id = item.google_event_id
                remote_event = None
                if g_event_id:
                    remote_event = self.gcal_service.get_event(g_event_id)
                
                if g_event_id and remote_event:
                    # Remote event exists. Check if any relevant field changed:
                    changed = (
                        remote_event.get("summary") != event_body["summary"] or
                        remote_event.get("location") != event_body["location"] or
                        remote_event.get("description") != event_body["description"]
                    )
                    
                    if changed:
                        self.gcal_service.patch_event(g_event_id, event_body)
                        updated_count += 1
                else:
                    # Remote event does not exist (or was deleted). Create it.
                    new_id = self.gcal_service.create_event(event_body)
                    self.repo.update_google_event_id(trip_id, item.activity_id, new_id)
                    self.repo.save_calendar_event(trip_id, item.day, item.activity, new_id, "primary")
                    created_count += 1

            self.repo.update_trip_status(trip_id, "SYNCED")
            
            # Log Sync Success
            self.repo.log_sync_event({
                "trip_id": trip_id,
                "user_id": user_id,
                "status": "SYNCED",
                "events_created": created_count,
                "events_updated": updated_count,
                "events_deleted": deleted_count,
                "error": None
            })
            
            return {
                "success": True,
                "message": f"Successfully synced {len(items)} events to Google Calendar."
            }

        except Exception as e:
            logger.error(f"Google Calendar Sync Failed: {e}")
            self.repo.update_trip_status(trip_id, "FAILED")
            self.repo.log_sync_event({
                "trip_id": trip_id,
                "user_id": user_id,
                "status": "FAILED",
                "events_created": created_count,
                "events_updated": updated_count,
                "events_deleted": deleted_count,
                "error": str(e)
            })
            return {"success": False, "message": f"Google Calendar API Error: {str(e)}"}

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
            lines.append("---")

        return "\n".join(lines)

    def _parse_natural_date(self, date_str: str) -> str:
        from rag_service import client
        prompt = (
            f"Convert the natural language travel date description '{date_str}' to a clean YYYY-MM-DD format.\n"
            "Assume the current context year is 2026. "
            "Return ONLY the YYYY-MM-DD string and nothing else (no formatting, no code block backticks)."
        )
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            val = response.choices[0].message.content.strip()
            val = val.replace("`", "").strip()
            return val
        except Exception:
            return date_str
