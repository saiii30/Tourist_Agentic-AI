from typing import TypedDict, Annotated
import operator


class AgentState(TypedDict):
    question: str
    routes: list[str]
    responses: Annotated[list[str], operator.add]
    answer: str
    city: str
    destination: str
    travel_date: str
    days: int
    budget: str
    travelers: int
    travel_style: str
    interests: str