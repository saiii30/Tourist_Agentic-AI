from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class TripCreateRequest(BaseModel):
    origin: str
    destination: str
    start_date: str
    end_date: str
    travelers: int = Field(..., ge=1)
    budget: float = Field(..., gt=0)
    interests: List[str] = []
    transport: str = "auto"
    food_preferences: str = "any"

class ItineraryItem(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    data: Dict[str, Any] = {}

class TripResponse(BaseModel):
    trip_id: str
    status: str = "pending"
    data: Dict[str, Any] = {}
