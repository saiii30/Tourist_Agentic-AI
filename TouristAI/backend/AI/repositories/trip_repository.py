import sys
import os
from typing import List, Optional
from datetime import datetime

# Adjust path to import correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.sqlite import SQLiteDatabase
from models.itinerary import Trip, ItineraryItem

class TripRepository:
    def __init__(self) -> None:
        SQLiteDatabase.initialize()

    def create_trip(self, trip: Trip) -> None:
        """
        Creates a new trip or updates an existing one in the SQLite database.
        """
        conn = SQLiteDatabase.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO trips 
                (trip_id, user_id, city, days, budget, travel_style, travelers, interests, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trip.trip_id, trip.user_id, trip.city, trip.days, trip.budget, 
                trip.travel_style, trip.travelers, trip.interests, trip.status, 
                trip.created_at, trip.updated_at
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_trip(self, trip_id: str) -> Optional[Trip]:
        """
        Fetches trip details from SQLite.
        """
        conn = SQLiteDatabase.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trips WHERE trip_id = ?", (trip_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Trip(**dict(row))
        return None

    def update_trip_status(self, trip_id: str, status: str) -> None:
        """
        Updates the status of a trip (e.g. 'draft', 'saved').
        """
        conn = SQLiteDatabase.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE trips 
                SET status = ?, updated_at = ?
                WHERE trip_id = ?
            """, (status, datetime.now().isoformat(), trip_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def save_itinerary_items(self, trip_id: str, items: List[ItineraryItem]) -> None:
        """
        Replaces all itinerary items for a trip.
        """
        conn = SQLiteDatabase.get_connection()
        cursor = conn.cursor()
        try:
            # Delete old items
            cursor.execute("DELETE FROM itineraries WHERE trip_id = ?", (trip_id,))
            
            for item in items:
                cursor.execute("""
                    INSERT INTO itineraries 
                    (trip_id, day, start_time, end_time, activity, location, category, restaurant, hotel, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trip_id, item.day, item.start_time, item.end_time, item.activity,
                    item.location, item.category, item.restaurant, item.hotel, item.notes
                ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_itinerary_items(self, trip_id: str) -> List[ItineraryItem]:
        """
        Gets all structured itinerary items for a trip sorted by day and start time.
        """
        conn = SQLiteDatabase.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM itineraries WHERE trip_id = ? ORDER BY day, start_time", (trip_id,))
        rows = cursor.fetchall()
        conn.close()
        return [ItineraryItem(**dict(row)) for row in rows]

    def delete_trip(self, trip_id: str) -> None:
        """
        Deletes a trip and all its associated itinerary items and calendar events mapping.
        """
        conn = SQLiteDatabase.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM trips WHERE trip_id = ?", (trip_id,))
            cursor.execute("DELETE FROM itineraries WHERE trip_id = ?", (trip_id,))
            cursor.execute("DELETE FROM calendar_events WHERE trip_id = ?", (trip_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def save_calendar_event(self, trip_id: str, day: int, activity: str, google_event_id: str, calendar_name: str) -> None:
        """
        Maps a Google Calendar Event ID to a trip's specific day and activity.
        """
        conn = SQLiteDatabase.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO calendar_events 
                (trip_id, day, activity, google_event_id, calendar_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                trip_id, day, activity, google_event_id, calendar_name, datetime.now().isoformat()
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_calendar_events(self, trip_id: str) -> List[dict]:
        """
        Fetches all Google Calendar mapped events for a trip.
        """
        conn = SQLiteDatabase.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM calendar_events WHERE trip_id = ?", (trip_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_calendar_event(self, trip_id: str, google_event_id: str) -> None:
        """
        Deletes calendar mapping for a specific Google event.
        """
        conn = SQLiteDatabase.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM calendar_events WHERE trip_id = ? AND google_event_id = ?", (trip_id, google_event_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_calendar_event_by_activity(self, trip_id: str, day: int, activity: str) -> Optional[dict]:
        """
        Fetches calendar event details by trip, day, and activity.
        """
        conn = SQLiteDatabase.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM calendar_events WHERE trip_id = ? AND day = ? AND activity = ?", (trip_id, day, activity))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
