from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class Trip(Base):
    __tablename__ = "trips"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    travelers = Column(Integer, nullable=False)
    budget = Column(Float, nullable=False)
    interests = Column(JSON, default=list)
    transport = Column(String, default="auto")
    food_preferences = Column(String, default="any")
    status = Column(String, default="queued")
    itinerary = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
