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
        if not items:
            return ""

        sorted_items = sorted(items, key=lambda x: (x.day, x.start_time or "99:99"))
        days_dict = {}
        for item in sorted_items:
            days_dict.setdefault(item.day, []).append(item)

        lines = []
        hotels = [item.hotel for item in sorted_items if item.hotel]
        default_hotel = hotels[0] if hotels else "Local Hotel"
        first_day = min(days_dict.keys())
        last_day = max(days_dict.keys())

        def clean(value) -> str:
            return (value or "").strip()

        def item_text(item: ItineraryItem) -> str:
            return " ".join([
                clean(item.activity),
                clean(item.location),
                clean(item.category),
                clean(item.notes),
            ]).lower()

        def is_category(item: ItineraryItem, *categories: str) -> bool:
            return clean(item.category).lower() in {category.lower() for category in categories}

        def is_transport(item: ItineraryItem) -> bool:
            return is_category(item, "transport", "transit", "travel", "transit/travel")

        def is_hotel(item: ItineraryItem) -> bool:
            return is_category(item, "hotel", "accommodation", "stay")

        def is_food(item: ItineraryItem) -> bool:
            return is_category(item, "food", "restaurant")

        def is_breakfast(item: ItineraryItem) -> bool:
            return "breakfast" in item_text(item) or (is_food(item) and clean(item.start_time) < "11:00")

        def is_lunch(item: ItineraryItem) -> bool:
            return "lunch" in item_text(item) or (is_food(item) and "11:00" <= clean(item.start_time) <= "16:00")

        def is_dinner(item: ItineraryItem) -> bool:
            return "dinner" in item_text(item) or (is_food(item) and clean(item.start_time) >= "17:00")

        def is_return_transport(item: ItineraryItem) -> bool:
            return is_transport(item) and ("return" in item_text(item) or item.day == last_day)

        def is_outbound_transport(item: ItineraryItem) -> bool:
            return is_transport(item) and item.day == first_day and not is_return_transport(item)

        def travel_inline(item: ItineraryItem) -> str:
            travel_time = clean(item.travel_time)
            if not travel_time or travel_time == "0 mins":
                return ""
            mode = clean(item.transport) or "Travel"
            distance = clean(getattr(item, "distance", None))
            parts = [mode, travel_time]
            if distance:
                parts.append(distance)
            icon = "🚶" if mode.lower() == "walking" else "🚖"
            return f"{icon} {' • '.join(parts)}\n"

        def transport_line(item: ItineraryItem) -> str:
            start = clean(item.start_time)
            end = clean(item.end_time)
            time = f"{start} - {end}: " if start or end else ""
            location = f" ({clean(item.location)})" if clean(item.location) else ""
            notes = f" {clean(item.notes)}" if clean(item.notes) else ""
            return f"- **{time}{clean(item.activity)}**{location}.{notes}"

        def activity_line(item: ItineraryItem) -> str:
            time = f"{clean(item.start_time)} - " if clean(item.start_time) else ""
            location = f" at {clean(item.location)}" if clean(item.location) else ""
            notes = f" {clean(item.notes)}" if clean(item.notes) else ""
            return f"{travel_inline(item)}📍 **{time}{clean(item.activity)}**{location}.{notes}"

        def meal_line(item: ItineraryItem) -> str:
            location = f" at {clean(item.location)}" if clean(item.location) else ""
            notes = f" {clean(item.notes)}" if clean(item.notes) else ""
            return f"{travel_inline(item)}{clean(item.activity)}{location}.{notes}"

        def take_first(day_items, used, predicate):
            for index, item in enumerate(day_items):
                if index not in used and predicate(item):
                    used.add(index)
                    return item
            return None

        def take_all(day_items, used, predicate):
            matches = []
            for index, item in enumerate(day_items):
                if index not in used and predicate(item):
                    used.add(index)
                    matches.append(item)
            return matches

        def hotel_name(item=None) -> str:
            if item and clean(item.hotel):
                return clean(item.hotel)
            if item and clean(item.activity):
                return clean(item.activity)
            return default_hotel

        def add_meal(title: str, item, fallback: str) -> None:
            lines.append(title)
            lines.append(meal_line(item) if item else fallback)
            lines.append("")

        def add_activity_section(title: str, section_items, fallback: str = None) -> None:
            lines.append(title)
            if section_items:
                for item in section_items:
                    lines.append(activity_line(item))
            elif fallback:
                lines.append(fallback)
            lines.append("")

        def morning_item(item: ItineraryItem) -> bool:
            return not is_transport(item) and not is_hotel(item) and not is_food(item) and clean(item.start_time) < "13:00"

        def afternoon_item(item: ItineraryItem) -> bool:
            return not is_transport(item) and not is_hotel(item) and not is_food(item) and "13:00" <= clean(item.start_time) < "17:00"

        def evening_item(item: ItineraryItem) -> bool:
            return not is_transport(item) and not is_hotel(item) and not is_food(item) and clean(item.start_time) >= "17:00"

        def other_activity(item: ItineraryItem) -> bool:
            return not is_transport(item) and not is_hotel(item) and not is_food(item)

        for day in sorted(days_dict.keys()):
            day_items = days_dict[day]
            used = set()
            lines.append(f"# Day {day}\n")

            outbound = take_all(day_items, used, is_outbound_transport)
            if outbound:
                lines.append("✈️ Travel to Destination")
                for item in outbound:
                    lines.append(transport_line(item))
                lines.append("")

            hotel_items = take_all(day_items, used, is_hotel)
            checkin_item = None
            overnight_item = None
            if hotel_items:
                checkin_item = next((item for item in hotel_items if "check" in item_text(item) or item.day == first_day), hotel_items[0])
                overnight_item = next((item for item in reversed(hotel_items) if "overnight" in item_text(item) or item.day != first_day), hotel_items[-1])

            if day == first_day:
                lines.append("🏨 Hotel Check-in")
                lines.append(hotel_name(checkin_item))
                if checkin_item and clean(checkin_item.location):
                    lines.append(clean(checkin_item.location))
                lines.append("Check in and freshen up.")
                lines.append("")
            else:
                lines.append("🏨 Hotel")
                lines.append(hotel_name(checkin_item or overnight_item))
                lines.append("")

            add_meal("🍳 Breakfast", take_first(day_items, used, is_breakfast), "Breakfast at the hotel or nearby cafe.")
            add_activity_section("🌅 Morning", take_all(day_items, used, morning_item), "- Explore local sightseeing viewpoints and temples.")
            add_meal("🍽 Lunch", take_first(day_items, used, is_lunch), "Enjoy delicious local cuisine at a recommended eatery.")
            add_activity_section("🌇 Afternoon", take_all(day_items, used, afternoon_item), "- Relax and stroll in the nearby shopping bazaar.")

            evening = take_all(day_items, used, evening_item)
            if day == last_day and not evening:
                lines.append("🛍 Free Time / Shopping")
                lines.append("- Keep this slot flexible for shopping, rest, or a final local stop.")
                lines.append("")
            else:
                add_activity_section("🌙 Evening", evening, "- Relax at local viewpoints or check out cultural shows.")

            add_meal("🍴 Dinner", take_first(day_items, used, is_dinner), "Dine at a local restaurant for a cozy dinner.")

            if day != last_day:
                lines.append("🌙 Overnight Stay")
                lines.append(hotel_name(overnight_item or checkin_item))
                lines.append("")

            return_transport = take_all(day_items, used, is_return_transport)
            if return_transport:
                lines.append("✈️ Return Journey")
                for item in return_transport:
                    lines.append(transport_line(item))
                lines.append("")

            leftovers = take_all(day_items, used, other_activity)
            if leftovers:
                add_activity_section("📌 Other Planned Stops", leftovers)

            lines.append("---")

        return "\n".join(lines)

    def _parse_natural_date(self, date_str: str) -> str:
        from rag_service import client
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        prompt = (
            f"Convert the natural language travel date description '{date_str}' to a clean YYYY-MM-DD format.\n"
            f"The current local date is {current_date_str}.\n"
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
