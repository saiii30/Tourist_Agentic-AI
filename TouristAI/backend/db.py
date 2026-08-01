# backend/db.py
import json
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .config import DATABASE_URL

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False, future=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create the trips table if it does not exist."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS trips (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    waypoints TEXT NOT NULL -- JSON-encoded list
                )
                """
            )
        )
        conn.commit()

# Initialize the DB schema on module import
init_db()
