import sys
import os
import json
import uuid
from typing import List, Optional
from datetime import datetime
import psycopg2.extras

# Adjust path to import correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.postgres import PostgresDatabase
from models.itinerary import Trip, ItineraryItem

class TripRepository:
    def __init__(self) -> None:
        PostgresDatabase.initialize()

    def create_trip(self, trip: Trip) -> None:
        """
        Creates a new trip or updates an existing one in the PostgreSQL database.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO trips 
                (trip_id, user_id, city, days, budget, travel_style, travelers, interests, status, travel_date, current_location, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (trip_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    city = EXCLUDED.city,
                    days = EXCLUDED.days,
                    budget = EXCLUDED.budget,
                    travel_style = EXCLUDED.travel_style,
                    travelers = EXCLUDED.travelers,
                    interests = EXCLUDED.interests,
                    status = EXCLUDED.status,
                    travel_date = EXCLUDED.travel_date,
                    current_location = EXCLUDED.current_location,
                    created_at = EXCLUDED.created_at,
                    updated_at = EXCLUDED.updated_at
            """, (
                trip.trip_id, trip.user_id, trip.city, trip.days, trip.budget, 
                trip.travel_style, trip.travelers, trip.interests, trip.status, 
                trip.travel_date, trip.current_location or "None", trip.created_at, trip.updated_at
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_trip(self, trip_id: str) -> Optional[Trip]:
        """
        Fetches trip details from PostgreSQL.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM trips WHERE trip_id = %s", (trip_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return Trip(**dict(row))
        return None

    def update_trip_status(self, trip_id: str, status: str) -> None:
        """
        Updates the status of a trip.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE trips 
                SET status = %s, updated_at = %s
                WHERE trip_id = %s
            """, (status, datetime.now().isoformat(), trip_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def save_itinerary_items(self, trip_id: str, items: List[ItineraryItem]) -> None:
        """
        Replaces all itinerary items for a trip.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        try:
            # Delete old items
            cursor.execute("DELETE FROM itineraries WHERE trip_id = %s", (trip_id,))
            
            for item in items:
                cursor.execute("""
                    INSERT INTO itineraries 
                    (trip_id, day, start_time, end_time, activity, location, category, restaurant, hotel, notes, activity_id, google_event_id,
                     hotel_id, restaurant_id, attraction_id, latitude, longitude, start_datetime, end_datetime, travel_time, transport, estimated_cost, status, distance)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    trip_id, item.day, item.start_time, item.end_time, item.activity,
                    item.location, item.category, item.restaurant, item.hotel, item.notes,
                    item.activity_id or str(uuid.uuid4()), item.google_event_id,
                    item.hotel_id, item.restaurant_id, item.attraction_id, item.latitude, item.longitude,
                    item.start_datetime, item.end_datetime, item.travel_time, item.transport, item.estimated_cost, item.status, item.distance
                ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_itinerary_items(self, trip_id: str) -> List[ItineraryItem]:
        """
        Gets all structured itinerary items for a trip sorted by day and start time.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM itineraries WHERE trip_id = %s ORDER BY day, start_time", (trip_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [ItineraryItem(**dict(row)) for row in rows]

    def delete_trip(self, trip_id: str) -> None:
        """
        Deletes a trip and all its associated itinerary items, details, versions, and calendar logs.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM trips WHERE trip_id = %s", (trip_id,))
            cursor.execute("DELETE FROM itineraries WHERE trip_id = %s", (trip_id,))
            cursor.execute("DELETE FROM trip_details WHERE trip_id = %s", (trip_id,))
            cursor.execute("DELETE FROM trip_versions WHERE trip_id = %s", (trip_id,))
            cursor.execute("DELETE FROM calendar_events WHERE trip_id = %s", (trip_id,))
            cursor.execute("DELETE FROM sync_logs WHERE trip_id = %s", (trip_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def save_calendar_event(self, trip_id: str, day: int, activity: str, google_event_id: str, calendar_name: str) -> None:
        """
        Maps a Google Calendar Event ID to a trip's specific day and activity.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO calendar_events 
                (trip_id, day, activity, google_event_id, calendar_name, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (trip_id, day, activity) DO UPDATE SET
                    google_event_id = EXCLUDED.google_event_id,
                    calendar_name = EXCLUDED.calendar_name,
                    created_at = EXCLUDED.created_at
            """, (
                trip_id, day, activity, google_event_id, calendar_name, datetime.now().isoformat()
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_calendar_events(self, trip_id: str) -> List[dict]:
        """
        Fetches all Google Calendar mapped events for a trip.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM calendar_events WHERE trip_id = %s", (trip_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(row) for row in rows]

    def delete_calendar_event(self, trip_id: str, google_event_id: str) -> None:
        """
        Deletes calendar mapping for a specific Google event.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM calendar_events WHERE trip_id = %s AND google_event_id = %s", (trip_id, google_event_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_calendar_event_by_activity(self, trip_id: str, day: int, activity: str) -> Optional[dict]:
        """
        Fetches calendar event details by trip, day, and activity.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM calendar_events WHERE trip_id = %s AND day = %s AND activity = %s", (trip_id, day, activity))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return dict(row)
        return None

    def save_trip_details(self, trip_id: str, details: dict) -> None:
        """
        Saves dynamic/enriched itinerary metadata like packing tips, budget summary, emergency etc.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO trip_details 
                (trip_id, packing_tips, packing_checklist, budget_summary, emergency_contacts, hotels, restaurants, weather_summary)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (trip_id) DO UPDATE SET
                    packing_tips = EXCLUDED.packing_tips,
                    packing_checklist = EXCLUDED.packing_checklist,
                    budget_summary = EXCLUDED.budget_summary,
                    emergency_contacts = EXCLUDED.emergency_contacts,
                    hotels = EXCLUDED.hotels,
                    restaurants = EXCLUDED.restaurants,
                    weather_summary = EXCLUDED.weather_summary
            """, (
                trip_id,
                json.dumps(details.get("packing", {})),
                json.dumps(details.get("packing_checklist", [])),
                json.dumps(details.get("budget_summary", {})),
                json.dumps(details.get("emergency", {})),
                json.dumps(details.get("hotels", [])),
                json.dumps(details.get("restaurants", [])),
                details.get("weather_summary", "")
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_trip_details(self, trip_id: str) -> Optional[dict]:
        """
        Loads dynamic/enriched itinerary metadata from DB.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM trip_details WHERE trip_id = %s", (trip_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            r = dict(row)
            try:
                return {
                    "packing": json.loads(r["packing_tips"]),
                    "packing_checklist": json.loads(r["packing_checklist"]),
                    "budget_summary": json.loads(r["budget_summary"]),
                    "emergency": json.loads(r["emergency_contacts"]),
                    "hotels": json.loads(r["hotels"]),
                    "restaurants": json.loads(r["restaurants"]),
                    "weather_summary": r["weather_summary"]
                }
            except Exception as e:
                print(f"Error parsing trip details from DB: {e}")
                return None
        return None

    def save_trip_version(self, trip_id: str, version: int, snapshot: str) -> None:
        """
        Saves a snapshot of the itinerary items for historical versioning.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO trip_versions (version_id, trip_id, version, created_at, itinerary_snapshot)
                VALUES (%s, %s, %s, %s, %s)
            """, (str(uuid.uuid4()), trip_id, version, datetime.now().isoformat(), snapshot))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_trip_versions(self, trip_id: str) -> List[dict]:
        """
        Fetches all versions of a trip.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM trip_versions WHERE trip_id = %s ORDER BY version DESC", (trip_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(row) for row in rows]

    def log_sync_event(self, log_entry: dict) -> None:
        """
        Logs a Google Calendar synchronization session details.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO sync_logs (trip_id, user_id, time, status, events_created, events_updated, events_deleted, error)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                log_entry.get("trip_id"),
                log_entry.get("user_id"),
                datetime.now().isoformat(),
                log_entry.get("status"),
                log_entry.get("events_created", 0),
                log_entry.get("events_updated", 0),
                log_entry.get("events_deleted", 0),
                log_entry.get("error")
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_sync_logs(self, trip_id: str) -> List[dict]:
        """
        Gets the sync logs for a trip.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM sync_logs WHERE trip_id = %s ORDER BY time DESC", (trip_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(row) for row in rows]

    def update_google_event_id(self, trip_id: str, activity_id: str, google_event_id: str) -> None:
        """
        Updates the google_event_id for an itinerary item.
        """
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE itineraries 
                SET google_event_id = %s
                WHERE trip_id = %s AND activity_id = %s
            """, (google_event_id, trip_id, activity_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
