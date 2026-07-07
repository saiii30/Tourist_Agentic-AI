from typing import TypedDict, Annotated
import operator


class AgentState(TypedDict):
    question: str
    routes: list[str]
    responses: Annotated[list[str], operator.add]
    answer: str
    city: str
    days: int
    budget: str
    travelers: int
    travel_style: str
    interests: str
    discover: list
    trip_id: str
    user_action: str
    start_date: str
    reminder_minutes: int
    google_auth_url: str
