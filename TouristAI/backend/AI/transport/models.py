from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NormalizedTicket(BaseModel):
    id: str
    mode: str                  # "Flight" | "Train" | "Bus"
    carrier: str               # e.g., "IndiGo", "SRS Travels"
    vehicle_type: str          # e.g., "Economy", "A/C Sleeper"
    departure: str             # e.g., "08:30"
    arrival: str               # e.g., "10:45"
    duration: str              # e.g., "2h 15m"
    price: float               # Raw price converted to float
    currency: str = "INR"
    rating: float = 0.0        # out of 5.0
    score: float = 0.0         # out of 100.0 (calculated ranking)
    booking_source: str        # "Google Flights", "RedBus", "ConfirmTkt"
    booking_url: str
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())

class TransportRequest(BaseModel):
    from_city: str
    to_city: str
    date: str                  # YYYY-MM-DD
    modes: List[str]           # ["Flight", "Train", "Bus"]
    budget: Optional[float] = None
    travelers: int = 1
    class_preference: Optional[str] = None
    time_preference: Optional[str] = None  # "Morning", "Afternoon", "Evening", "Night"
    preferred_mode: Optional[str] = None
