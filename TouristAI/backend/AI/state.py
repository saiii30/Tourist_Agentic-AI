from typing import TypedDict, Annotated, List, Optional
import operator


class Notification(TypedDict):
    id: str
    type: str          # 'weather', 'activity', 'hotel', 'restaurant', 'nearby', 'calendar', 'trip_start', 'trip_end', 'packing', 'general'
    source: str        # 'weather', 'itinerary', 'calendar', 'hotel', 'restaurant', 'nearby'
    priority: str      # 'critical', 'high', 'medium', 'low'
    trigger: str       # 'immediate', 'trip_created', 'trip_started', '1_day_before', '2_hours_before', '30_minutes_before', 'arrival', 'departure', 'meal_time', 'evening', 'calendar_saved'
    event_time: Optional[str]
    title: str
    text: str
    voice: str
    play_voice: bool
    spoken: bool
    status: str        # 'pending', 'active', 'spoken', 'dismissed', 'expired'
    action: Optional[dict]  # Optional action config, e.g. {"label": "View Hotel", "type": "hotel"}


class AgentState(TypedDict):
    question: str
    routes: list[str]
    responses: Annotated[list[str], operator.add]
    answer: str
    city: str
    days: int
    destination: str
    travel_date : str
    budget: str
    travelers: int
    travel_style: str
    interests: str
    trip_id: str
    user_action: str
    start_date: str
    reminder_minutes: int
    google_auth_url: str
    hotels_data: list[dict]
    restaurants_data: list[dict]
    nearby_data: list[dict]
    weather_data: dict
    notifications: List[Notification]
    active_agent: str
    checkin: str
    checkout: str
    guests: int
    rooms: int
    breakfast: str
    hotel_type: str
    amenities: str
    budget_per_person: str
    diet: str
    cuisine: str
    meal_time: str
    family_friendly: str
    outdoor_seating: str
    allergies: str
    max_distance: str
    price_preference: str
    traveler_type: str
    include_hotel: str
    include_transport: str
    shopping_budget: str
    nearbyResult: dict | None
    checkin: str
    checkout: str
    guests: int
    rooms: int
    breakfast: str
    hotel_type: str
    amenities: str
    budget_per_person: str
    diet: str
    cuisine: str
    meal_time: str
    family_friendly: str
    outdoor_seating: str
    allergies: str
    max_distance: str
    price_preference: str
    traveler_type: str
    include_hotel: str
    include_transport: str
    shopping_budget: str
