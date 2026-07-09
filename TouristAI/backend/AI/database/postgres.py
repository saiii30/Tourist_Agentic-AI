import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Load environmental variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "tourist_ai")

class PostgresDatabase:
    @staticmethod
    def get_connection():
        """
        Returns a PostgreSQL connection with DictCursor configured by default.
        """
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME
        )
        return conn

    @staticmethod
    def initialize() -> None:
        """
        Initializes PostgreSQL database tables for the itinerary lifecycle if they do not exist.
        Auto-creates the database if it doesn't exist yet.
        """
        # Step 1: Check/Create Database
        try:
            conn = PostgresDatabase.get_connection()
            conn.close()
        except psycopg2.OperationalError as oe:
            # If the database does not exist, connect to 'postgres' database and create it
            if "does not exist" in str(oe):
                print(f"Database '{DB_NAME}' does not exist. Auto-creating...")
                temp_conn = psycopg2.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    dbname="postgres"
                )
                temp_conn.autocommit = True
                temp_cursor = temp_conn.cursor()
                temp_cursor.execute(f'CREATE DATABASE "{DB_NAME}"')
                temp_cursor.close()
                temp_conn.close()
                print(f"Database '{DB_NAME}' created successfully.")
            else:
                raise oe

        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        
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

        # Alter table upgrades (safely handles existing tables prior to travel_date column)
        cursor.execute("ALTER TABLE trips ADD COLUMN IF NOT EXISTS travel_date TEXT")

        # 3. Itinerary table (stored as structured records)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS itineraries (
                id SERIAL PRIMARY KEY,
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

        # Upgrades for itineraries table
        cursor.execute("ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS activity_id TEXT")
        cursor.execute("ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS google_event_id TEXT")
        cursor.execute("ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS hotel_id TEXT")
        cursor.execute("ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS restaurant_id TEXT")
        cursor.execute("ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS attraction_id TEXT")
        cursor.execute("ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS latitude REAL")
        cursor.execute("ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS longitude REAL")
        cursor.execute("ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS start_datetime TEXT")
        cursor.execute("ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS end_datetime TEXT")
        cursor.execute("ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS travel_time TEXT")
        cursor.execute("ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS transport TEXT")
        cursor.execute("ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS estimated_cost REAL")
        cursor.execute("ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS status TEXT")


        # 4. Trip Details metadata table
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

        # 6. Calendar Mapping table (Supports both Google Calendar sync columns and legacy chatbot save columns)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id SERIAL PRIMARY KEY,
                trip_id TEXT,
                day INTEGER,
                activity TEXT,
                google_event_id TEXT,
                calendar_name TEXT,
                created_at TEXT,
                trip_name TEXT,
                day_num INTEGER,
                time_slot TEXT,
                time_range TEXT,
                details TEXT,
                FOREIGN KEY (trip_id) REFERENCES trips(trip_id) ON DELETE CASCADE
            )
        """)

        # 7. Sync History Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_logs (
                id SERIAL PRIMARY KEY,
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
        
        # 8. Places table for fallback searches (referenced by calendar agent)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS places (
                id SERIAL PRIMARY KEY,
                city TEXT,
                name TEXT,
                place_type TEXT,
                description TEXT,
                rating REAL
            )
        """)

        # 9. Guided Planning state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guided_trip_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
