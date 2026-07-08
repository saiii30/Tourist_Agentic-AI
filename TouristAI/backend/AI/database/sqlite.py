import os
import sqlite3

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tourist_ai.db"))

class SQLiteDatabase:
    @staticmethod
    def get_connection() -> sqlite3.Connection:
        """
        Returns a sqlite3 connection with Row factory configured.
        """
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def initialize() -> None:
        """
        Initializes database tables for the itinerary lifecycle if they do not exist.
        """
        conn = SQLiteDatabase.get_connection()
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        # 1. Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT
            )
        """)

        # 2. Trips table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                trip_id TEXT PRIMARY KEY,
                user_id TEXT,
                city TEXT,
                days INTEGER,
                budget TEXT,
                travel_style TEXT,
                travelers INTEGER,
                interests TEXT,
                status TEXT,
                travel_date TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Upgrades for Trips table if it existed prior to adding travel_date
        try:
            cursor.execute("ALTER TABLE trips ADD COLUMN travel_date TEXT")
        except sqlite3.OperationalError:
            # Already exists
            pass

        # 3. Itinerary table (stored as structured records)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS itineraries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id TEXT,
                day INTEGER,
                start_time TEXT,
                end_time TEXT,
                activity TEXT,
                location TEXT,
                category TEXT,
                restaurant TEXT,
                hotel TEXT,
                notes TEXT,
                activity_id TEXT,
                google_event_id TEXT,
                FOREIGN KEY (trip_id) REFERENCES trips(trip_id) ON DELETE CASCADE
            )
        """)

        # Upgrades for Itinerary table if they existed prior
        try:
            cursor.execute("ALTER TABLE itineraries ADD COLUMN activity_id TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE itineraries ADD COLUMN google_event_id TEXT")
        except sqlite3.OperationalError:
            pass

        # 4. Trip Details metadata table (stores serialized tips, packing lists, weather, emergency, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trip_details (
                trip_id TEXT PRIMARY KEY,
                packing_tips TEXT,
                packing_checklist TEXT,
                budget_summary TEXT,
                emergency_contacts TEXT,
                hotels TEXT,
                restaurants TEXT,
                weather_summary TEXT,
                FOREIGN KEY (trip_id) REFERENCES trips(trip_id) ON DELETE CASCADE
            )
        """)

        # 5. Trip Versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trip_versions (
                version_id TEXT PRIMARY KEY,
                trip_id TEXT,
                version INTEGER,
                created_at TEXT,
                itinerary_snapshot TEXT,
                FOREIGN KEY (trip_id) REFERENCES trips(trip_id) ON DELETE CASCADE
            )
        """)

        # 6. SQLite Calendar Mapping table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id TEXT,
                day INTEGER,
                activity TEXT,
                google_event_id TEXT,
                calendar_name TEXT,
                created_at TEXT,
                FOREIGN KEY (trip_id) REFERENCES trips(trip_id) ON DELETE CASCADE
            )
        """)

        # 7. Sync History Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id TEXT,
                user_id TEXT,
                time TEXT,
                status TEXT,
                events_created INTEGER,
                events_updated INTEGER,
                events_deleted INTEGER,
                error TEXT,
                FOREIGN KEY (trip_id) REFERENCES trips(trip_id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        conn.close()
