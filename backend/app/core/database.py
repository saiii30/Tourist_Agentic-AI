import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Default to PostgreSQL (docker) for dev, fallback to SQLite for unit tests
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/tourist_ai"
)

engine = create_engine(
    DATABASE_URL,
    # For SQLite we need to allow multithread; for Postgres not needed
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
