from langgraph.graph import StateGraph, END
from langgraph.constants import Send

from state import AgentState
from supervisor import route_question, extract_query_details, get_guided_state, get_next_missing_field

from agents.restaurant_agent import restaurant_agent
from agents.hotel_agent import hotel_agent
from agents.nearby_agent import nearby_agent
from agents.weather_agent import weather_agent
from agents.general_agent import general_agent
from agents.calendar_agent import calendar_agent
from agents.transport_agent import transport_agent
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph"))
from calendar_nodes import (
    calendar_preview_node,
    modify_itinerary_node,
    save_itinerary_node,
    google_calendar_node,
    regenerate_itinerary_node,
    delete_itinerary_node
)
from rag_service import client



builder = StateGraph(AgentState)


def supervisor_node(state):

    # Route first to update database state
    routes = route_question(state)
    
    # Direct routing for active preview lifecycle actions
    lifecycle_actions = ["save_itinerary", "google_calendar", "modify_itinerary", "regenerate_itinerary", "delete_itinerary"]
    if len(routes) == 1 and routes[0] in lifecycle_actions:
        return {
            **state,
            "routes": routes
        }

    g_state = get_guided_state()
    is_active = g_state.get("is_active") == "1"
    
    if is_active or routes == ["merge"]:
        missing_key, missing_prompt = get_next_missing_field(g_state)
        return {
            **state,
            "city": "None",
            "days": 3,
            "budget": "None",
            "travelers": 1,
            "travel_style": "None",
            "interests": "None",
            "answer": missing_prompt,
            "routes": ["merge"]
        }
        
    if not is_active and len(routes) > 1 and "calendar" in routes:
        city = g_state.get("destination", "None")
        days = int(g_state.get("days", 3))
        budget = g_state.get("budget", "None")
        travelers = int(g_state.get("travelers", 1))
        travel_style = g_state.get("travel_style", "None")
        interests = g_state.get("interests", "None")
        travel_date = g_state.get("travel_date", "None")
        
        compiled_question = (
            f"Plan a {days}-day trip to {city} starting on {travel_date}. "
            f"Travel style is {travel_style}, travelers is {travelers}, budget is {budget}, interests are {interests}."
        )
        return {
            **state,
            "question": compiled_question,
            "city": city,
            "days": days,
            "budget": budget,
            "travelers": travelers,
            "travel_style": travel_style,
            "interests": interests,
            "routes": routes
        }

    details = extract_query_details(state["question"])
    stateless_routes = route_question(state, details)
    return {
        **state,
        "city": details.get("city", "None"),
        "days": details.get("days", 3),
        "budget": "None",
        "travelers": 1,
        "travel_style": "None",
        "interests": "None",
        "routes": stateless_routes
    }


def restaurant_node(state):
    answer = restaurant_agent(state["question"], state.get("city", "None"), state.get("interests", "None"), state.get("budget", "None"))
    text = answer.get("answer") if isinstance(answer, dict) else answer
    source = answer.get("source", "Groq") if isinstance(answer, dict) else "Groq"
    data = answer.get("data", []) if isinstance(answer, dict) else []

    return {
        "responses": [
            f"Restaurant suggestions:\n{text}\n[SOURCE:{source}]"
        ],
        "restaurants_data": data
    }


def hotel_node(state):
    answer = hotel_agent(state["question"], state.get("city", "None"), state.get("budget", "None"), state.get("travelers", 1))
    
    if isinstance(answer, dict):
        text = answer.get("hotels") or answer.get("answer") or answer.get("message", "Could not retrieve hotel info.")
        source = answer.get("source", "Groq")
        data = answer.get("data", [])
    else:
        text = str(answer)
        source = "Groq"
        data = []

    return {
        "responses": [
            f"Hotel suggestions:\n{text}\n[SOURCE:{source}]"
        ],
        "hotels_data": data
    }


def nearby_node(state):
    answer = nearby_agent(state["question"], state.get("city", "None"), state.get("interests", "None"))
    text = answer.get("answer") if isinstance(answer, dict) else answer
    source = answer.get("source", "Groq") if isinstance(answer, dict) else "Groq"
    data = answer.get("data", []) if isinstance(answer, dict) else []

    return {
        "responses": [
            f"Nearby Places to visit:\n{text}\n[SOURCE:{source}]"
        ],
        "nearby_data": data
    }


def weather_node(state):
    answer = weather_agent(state["question"], state.get("city", "None"))
    text = answer.get("text") if isinstance(answer, dict) else answer
    data = answer.get("data", {}) if isinstance(answer, dict) else {}

    return {
        "responses": [
            f"Weather:\n{text}"
        ],
        "weather_data": data
    }


def general_node(state):
    answer = general_agent(state)

    return {
        "responses": [
            f"{answer.get('answer')}\n[SOURCE:{answer.get('source', 'Groq')}]"
        ]
    }


def transport_node(state):
    # Extract source, destination, and date from the state if available
    # The supervisor logic for guided trips populates these.
    # For stateless queries, we can enhance `extract_query_details` to find them.
    source_city = state.get("city", "None") # 'city' is often used as the primary location/source
    destination_city = state.get("destination", "None")
    travel_date = state.get("travel_date", "None")

    answer = transport_agent(
        state["question"],
        source=source_city,
        destination=destination_city,
        date=travel_date
    )

    # The transport_agent can return a string or a dict. We need to handle both.
    text = answer.get("answer") if isinstance(answer, dict) else str(answer)
    source = answer.get("source", "transport_api") if isinstance(answer, dict) else "Groq"

    return {
        "responses": [
            f"Transport options:\n{text}\n[SOURCE:{source}]"
        ]
    }

def calendar_node(state):
    answer = calendar_agent(
        question=state["question"],
        city=state.get("city", "None"),
        days=state.get("days", 3),
        interests=state.get("interests", "None"),
        travel_style=state.get("travel_style", "None"),
        budget=state.get("budget", "None"),
        hotels_data=state.get("hotels_data"),
        restaurants_data=state.get("restaurants_data"),
        nearby_data=state.get("nearby_data"),
        weather_data=state.get("weather_data")
    )

    return {
        "responses": [
            f"Calendar:\n{answer}"
        ]
    }


def merge_node(state):
    print(f"[DEBUG] Merge Node state hotels_data: {len(state.get('hotels_data') or [])} items")
    print(f"[DEBUG] Merge Node state restaurants_data: {len(state.get('restaurants_data') or [])} items")
    print(f"[DEBUG] Merge Node state nearby_data: {len(state.get('nearby_data') or [])} items")

    # If there is only one response, return directly
    if len(state["responses"]) <= 1:
        context = "\n\n".join(state["responses"])
        if not context.strip():
            return {"answer": state.get("answer", "")}
        return {"answer": context}

    # If the destination city is not specified
    if state.get("city", "None") == "None":
        return {
            "answer": (
                "I would love to help you plan your trip! However, could you please specify which city or "
                "destination you are planning to visit? Once you tell me the destination (e.g., *'Plan a 1-day trip "
                "to Madurai'* or *'weather in Ooty'*), I will generate a complete customized itinerary, check "
                "the weather forecast, and recommend hotels and restaurants for you!"
            )
        }

    budget_val = state.get("budget", "None")
    budget_description = "budget-friendly"
    budget_limit_text = "strictly under ₹5,000"
    if budget_val.lower() == "moderate":
        budget_description = "moderate budget"
        budget_limit_text = "between ₹5,000 and ₹15,000"
    elif budget_val.lower() == "luxury":
        budget_description = "luxury"
        budget_limit_text = "above ₹15,000"

    city = state.get("city", "None").title()
    days = state.get("days", 3)
    travelers = state.get("travelers", 1)
    travel_style = state.get("travel_style", "None")
    interests = state.get("interests", "None")

    sections = {}
    for r in state["responses"]:
        if r.startswith("Restaurant suggestions:\n"): sections["restaurants"] = r.split(":\n", 1)[1]
        elif r.startswith("Hotel suggestions:\n"): sections["hotels"] = r.split(":\n", 1)[1]
        elif r.startswith("Nearby Places to visit:\n"): sections["places"] = r.split(":\n", 1)[1]
        elif r.startswith("Weather:\n"): sections["weather"] = r.split(":\n", 1)[1]

    # Collect compiled suggestions for the calendar agent
    other_agent_info = f"Hotels: {sections.get('hotels', 'None')}\nRestaurants: {sections.get('restaurants', 'None')}\nPlaces: {sections.get('places', 'None')}"
    
    # Synchronously call calendar_agent with the combined context from other agents
    from agents.calendar_agent import calendar_agent
    calendar_text = calendar_agent(
        question=state["question"], 
        city=state.get("city", "None"), 
        days=days, 
        interests=interests, 
        travel_style=travel_style, 
        budget=budget_val, 
        hotels_data=state.get("hotels_data"),
        restaurants_data=state.get("restaurants_data"),
        nearby_data=state.get("nearby_data"),
        weather_data=state.get("weather_data"),
        other_agent_info=other_agent_info
    )

    # Process calendar items
    import json
    try:
        if "{" in calendar_text or "[" in calendar_text:
            cleaned_cal = calendar_text[calendar_text.find("["):calendar_text.rfind("]")+1]
            calendar_items = json.loads(cleaned_cal)
        else:
            calendar_items = []
    except Exception as e:
        print(f"Failed to parse calendar items in merge_node: {e}")
        calendar_items = []

    # Store items natively in state for immediate ingestion
    from supervisor import update_guided_state
    update_guided_state("last_itinerary_items", json.dumps(calendar_items))

    # Format the calendar markdown
    calendar_md_lines = []
    current_day = 0
    for item in calendar_items:
        if item.get("day") != current_day:
            current_day = item.get("day")
            calendar_md_lines.append(f"\n🗓 **Day {current_day}**")
        
        start = item.get("start_time", "")
        # Convert 24h to 12h for pretty print
        try:
            from datetime import datetime
            pretty_time = datetime.strptime(start, "%H:%M").strftime("%I:%M %p") if start else ""
        except:
            pretty_time = start

        end = item.get("end_time", "")
        try:
            from datetime import datetime
            pretty_end = datetime.strptime(end, "%H:%M").strftime("%I:%M %p") if end else ""
            if pretty_end:
                pretty_time += f" - {pretty_end}"
        except:
            pass

        period = "Morning"
        if start and len(start) >= 5:
            hour = int(start.split(':')[0])
            if hour >= 17: period = "Evening"
            elif hour >= 12: period = "Afternoon"
            
        calendar_md_lines.append(f"**{period}{' (' + pretty_time + ')' if pretty_time else ''}**")
        calendar_md_lines.append(f"**{item.get('activity')}**")
        if item.get('notes'):
            calendar_md_lines.append(f"*{item.get('notes')}*")
        calendar_md_lines.append("")
        
    calendar_formatted = "\n".join(calendar_md_lines)

    synthesis = f"""📍 **{city}**

Great! I've planned a {days}-day {city} trip for {travelers} traveler(s) (style: {travel_style}) who enjoy {interests}.

🌤 **Weather in {city}**
{sections.get('weather', 'Not available')}

📅 **Itinerary Schedule**
{calendar_formatted}

*(Note: You can view details and comparison options for recommended hotels, dining spots, and attractions in the panels below. Select an action to proceed.)*"""

    update_guided_state("last_itinerary", synthesis)

    return {
        "answer": synthesis,
        "routes": ["calendar_preview"]
    }
    
builder.add_node(
    "supervisor",
    supervisor_node
)

builder.add_node(
    "restaurant",
    restaurant_node
)

builder.add_node(
    "hotel",
    hotel_node
)

builder.add_node(
    "nearby",
    nearby_node
)

builder.add_node(
    "train",
    transport_node
)


builder.add_node(
    "weather",
    weather_node
)


builder.add_node(
    "general",
    general_node
)






builder.add_node(
    "merge",
    merge_node
)

builder.add_node("calendar_preview", calendar_preview_node)
builder.add_node("modify_itinerary", modify_itinerary_node)
builder.add_node("save_itinerary", save_itinerary_node)
builder.add_node("google_calendar", google_calendar_node)
builder.add_node("regenerate_itinerary", regenerate_itinerary_node)
builder.add_node("delete_itinerary", delete_itinerary_node)

builder.set_entry_point(
    "supervisor"
)

def router(state):
    sends = []

    for route in state["routes"]:
        if route != "calendar":
            sends.append(
                Send(route, state)
            )

    return sends

builder.add_conditional_edges(
    "supervisor",
    router
)

builder.add_edge(
    "restaurant",
    "merge"
)

builder.add_edge(
    "hotel",
    "merge"
)

builder.add_edge(
    "nearby",
    "merge"
)
builder.add_edge(
    "train",
    "merge"
)


builder.add_edge(
    "weather",
    "merge"
)


builder.add_edge(
    "general",
    "merge"
)




def merge_router(state):
    routes = state.get("routes", [])
    if "calendar" in routes or "calendar_preview" in routes:
        return "calendar_preview"
    return END

builder.add_conditional_edges(
    "merge",
    merge_router,
    {
        "calendar_preview": "calendar_preview",
        END: END
    }
)

def regenerate_router(state):
    sends = []
    for route in state.get("routes", []):
        sends.append(Send(route, state))
    return sends

builder.add_conditional_edges(
    "regenerate_itinerary",
    regenerate_router
)

builder.add_edge("calendar_preview", END)
builder.add_edge("save_itinerary", END)
builder.add_edge("google_calendar", END)
builder.add_edge("delete_itinerary", END)
builder.add_edge("modify_itinerary", "calendar_preview")

graph = builder.compile()