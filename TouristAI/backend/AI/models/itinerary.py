from pydantic import BaseModel, Field
from typing import List, Optional

class ItineraryItem(BaseModel):
    id: Optional[int] = None
    trip_id: Optional[str] = None
    day: int = Field(..., description="Day number of the activity, 1-indexed")
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")
    activity: str = Field(..., description="Name/summary of the activity")
    location: str = Field(..., description="Location of the activity")
    category: str = Field(..., description="Category, e.g., Sightseeing, Food, Shopping, Relaxation, Transit")
    restaurant: Optional[str] = Field(None, description="Name of restaurant if category is Food")
    hotel: Optional[str] = Field(None, description="Name of hotel if staying here")
    notes: Optional[str] = Field(None, description="Additional context or descriptions")
    activity_id: Optional[str] = None
    google_event_id: Optional[str] = None
    hotel_id: Optional[str] = None
    restaurant_id: Optional[str] = None
    attraction_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    start_datetime: Optional[str] = None
    end_datetime: Optional[str] = None
    travel_time: Optional[str] = None
    transport: Optional[str] = None
    estimated_cost: Optional[float] = None
    status: Optional[str] = "pending"


class Trip(BaseModel):
    trip_id: str
    user_id: str
    city: str
    days: int
    budget: str
    travel_style: str
    travelers: int
    interests: str
    status: str = "GENERATED"
    travel_date: Optional[str] = None
    created_at: str
    updated_at: str

class TripWithItinerary(BaseModel):
    trip: Trip
    itinerary: List[ItineraryItem]
