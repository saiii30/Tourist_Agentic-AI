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

        # 1. Trips table
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
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # 2. Itinerary table (stored as structured records)
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
                FOREIGN KEY (trip_id) REFERENCES trips(trip_id) ON DELETE CASCADE
            )
        """)

        # 3. SQLite Calendar Mapping table
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

        conn.commit()
        conn.close()
