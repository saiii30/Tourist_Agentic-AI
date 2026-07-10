# from intelligence.discover import get_discover_places
# from services.response_builder import ResponseBuilder


# def discover_agent(question, city):
#     discover_result = get_discover_places(city)
#     print("="*50)
#     print("DISCOVER AGENT CALLED")
#     print("QUESTION:", question)
#     print("CITY:", city)
#     print("="*50)

#     if not discover_result:
#         return f"Sorry, I couldn't find any tourist attractions for **{city}**."

#     return ResponseBuilder.build(city, discover_result)


from intelligence.discover import get_discover_places
from services.response_builder import ResponseBuilder
from services.attraction_builder import AttractionBuilder


def discover_agent(question, city):

    discover_result = get_discover_places(city)

    print("=" * 50)
    print("DISCOVER AGENT CALLED")
    print("QUESTION:", question)
    print("CITY:", city)
    print("=" * 50)

    if not discover_result:
        return {
            "answer": f"Sorry, I couldn't find any tourist attractions for **{city}**.",
            "attractions": []
        }

    return {
        "answer": ResponseBuilder.build(city, discover_result),
        "attractions": AttractionBuilder.build(city, discover_result)
    }