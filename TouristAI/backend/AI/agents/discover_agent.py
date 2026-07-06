from intelligence.discover import get_discover_places
from services.response_builder import ResponseBuilder


def discover_agent(question, city):
    discover_result = get_discover_places(city)

    if not discover_result:
        return f"Sorry, I couldn't find any tourist attractions for **{city}**."

    return ResponseBuilder.build(city, discover_result)
