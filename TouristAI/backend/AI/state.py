from typing import TypedDict, Annotated
import operator


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