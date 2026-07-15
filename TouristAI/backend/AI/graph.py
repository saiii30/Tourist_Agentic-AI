from langgraph.graph import StateGraph, END
from langgraph.constants import Send

from state import AgentState
from supervisor import (
    route_question,
    extract_query_details,
    get_guided_state,
    get_next_missing_field,
    get_active_agent_question,
    get_agent_context,
    update_guided_state,
)

from agents.restaurant_agent import restaurant_agent
from agents.hotel_agent import hotel_agent
from agents.nearby_agent import nearby_agent
from agents.weather_agent import weather_agent
from agents.general_agent import general_agent
from agents.calendar_agent import calendar_agent
from agents.transport_agent import transport_agent
from agents.voice_notification_agent import generate_voice_notifications
from agents.budget_agent import budget_agent
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
    g_state = get_guided_state()
    active_agent, missing_key, missing_prompt = get_active_agent_question(g_state)
    if active_agent and missing_key:
        return {
            **state,
            "answer": missing_prompt,
            "routes": ["merge"]
        }
    completed_agent = g_state.get("last_completed_agent")
    if completed_agent and routes:
        agent_context = get_agent_context(completed_agent, g_state)
        update_guided_state("last_completed_agent", "")
        city = agent_context.get("city") or agent_context.get("destination") or state.get("city", "None")
        budget = agent_context.get("budget") or agent_context.get("budget_level") or state.get("budget", "None")
        interests = agent_context.get("interests") or state.get("interests", "None")
        days = agent_context.get("days") or state.get("days", 3)
        travelers = agent_context.get("travelers") or agent_context.get("guests") or state.get("travelers", 1)
        try:
            days = int(days)
        except Exception:
            days = 3
        try:
            travelers = int(travelers)
        except Exception:
            travelers = 1

        travel_date = agent_context.get("travel_date") or state.get("travel_date", "None")
        question = state.get("question")
        if completed_agent == "calendar":
            travel_style = agent_context.get("travel_style", "None")
            question = (
                f"Plan a {days}-day trip to {city} starting on {travel_date}. "
                f"Travel style is {travel_style}, travelers is {travelers}, budget is {budget}, interests are {interests}."
            )
        elif completed_agent == "hotel":
            checkin = agent_context.get("checkin", "None")
            checkout = agent_context.get("checkout", "None")
            guests = agent_context.get("guests") or travelers
            breakfast = agent_context.get("breakfast", "None")
            hotel_type = agent_context.get("hotel_type", "None")
            amenities = agent_context.get("amenities", "None")
            
            question = f"Suggest hotels in {city} for {guests} guests"
            if checkin and checkin != "None":
                question += f" checking in on {checkin}"
            if checkout and checkout != "None":
                question += f" checking out on {checkout}"
            if budget and budget != "None":
                question += f" with {budget} budget"
            
            prefs = []
            if hotel_type and hotel_type != "None":
                prefs.append(f"type: {hotel_type}")
            if breakfast and breakfast != "None":
                prefs.append(f"breakfast: {breakfast}")
            if amenities and amenities != "None":
                prefs.append(f"amenities: {amenities}")
            if prefs:
                question += f". Preferences: {', '.join(prefs)}"
                
        elif completed_agent == "restaurant":
            budget_per_person = agent_context.get("budget_per_person", "None")
            diet = agent_context.get("diet", "None")
            cuisine = agent_context.get("cuisine", "None")
            meal_time = agent_context.get("meal_time", "None")
            family_friendly = agent_context.get("family_friendly", "None")
            outdoor_seating = agent_context.get("outdoor_seating", "None")
            allergies = agent_context.get("allergies", "None")
            
            question = f"Suggest restaurants in {city}"
            if cuisine and cuisine != "None":
                question += f" serving {cuisine} cuisine"
            if meal_time and meal_time != "None":
                question += f" for {meal_time}"
            if diet and diet != "None":
                question += f" with {diet} food option"
            
            prefs = []
            if budget_per_person and budget_per_person != "None":
                prefs.append(f"budget per person: {budget_per_person}")
            if family_friendly and family_friendly != "None":
                prefs.append(f"family friendly: {family_friendly}")
            if outdoor_seating and outdoor_seating != "None":
                prefs.append(f"outdoor seating: {outdoor_seating}")
            if allergies and allergies != "None":
                prefs.append(f"allergies: {allergies}")
            if prefs:
                question += f". Preferences: {', '.join(prefs)}"
                
        elif completed_agent in {"attraction", "nearby"}:
            max_distance = agent_context.get("max_distance", "None")
            price_preference = agent_context.get("price_preference", "None")
            traveler_type = agent_context.get("traveler_type", "None")
            
            question = f"Suggest tourist attractions in {city}"
            if interests and interests != "None":
                question += f" for {interests}"
            
            prefs = []
            if max_distance and max_distance != "None":
                prefs.append(f"max distance: {max_distance}")
            if price_preference and price_preference != "None":
                prefs.append(f"pricing: {price_preference}")
            if traveler_type and traveler_type != "None":
                prefs.append(f"travelers: {traveler_type}")
            if prefs:
                question += f". Preferences: {', '.join(prefs)}"

        return {
            **state,
            "question": question,
            "city": city,
            "destination": agent_context.get("destination", city),
            "days": days,
            "budget": budget,
            "travelers": travelers,
            "travel_style": agent_context.get("travel_style", state.get("travel_style", "None")),
            "interests": interests,
            "checkin": agent_context.get("checkin", "None"),
            "checkout": agent_context.get("checkout", "None"),
            "guests": travelers,
            "breakfast": agent_context.get("breakfast", "None"),
            "hotel_type": agent_context.get("hotel_type", "None"),
            "amenities": agent_context.get("amenities", "None"),
            "budget_per_person": agent_context.get("budget_per_person", "None"),
            "diet": agent_context.get("diet", "None"),
            "cuisine": agent_context.get("cuisine", "None"),
            "meal_time": agent_context.get("meal_time", "None"),
            "family_friendly": agent_context.get("family_friendly", "None"),
            "outdoor_seating": agent_context.get("outdoor_seating", "None"),
            "allergies": agent_context.get("allergies", "None"),
            "max_distance": agent_context.get("max_distance", "None"),
            "price_preference": agent_context.get("price_preference", "None"),
            "traveler_type": agent_context.get("traveler_type", "None"),
            "include_hotel": agent_context.get("include_hotel", "Yes"),
            "include_transport": agent_context.get("include_transport", "Yes"),
            "shopping_budget": agent_context.get("shopping_budget", "Yes"),
            "travel_date": travel_date,
            "routes": routes
        }
    
    # Direct routing for active preview lifecycle actions
    lifecycle_actions = ["save_itinerary", "google_calendar", "modify_itinerary", "regenerate_itinerary", "delete_itinerary"]
    if len(routes) == 1 and routes[0] in lifecycle_actions:
        return {
            **state,
            "routes": routes
        }

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
    enriched_question = state["question"]
    restaurant_preferences = [
        state.get("diet", "None"),
        state.get("cuisine", "None"),
        state.get("meal_time", "None"),
        state.get("family_friendly", "None"),
        state.get("outdoor_seating", "None"),
        state.get("allergies", "None"),
    ]
    preference_text = ", ".join([p for p in restaurant_preferences if p and p != "None"])
    if preference_text:
        enriched_question = f"{enriched_question}. Preferences: {preference_text}"

    budget = state.get("budget", "None")
    if budget == "None" and state.get("budget_per_person", "None") != "None":
        budget = state.get("budget_per_person")

    answer = restaurant_agent(enriched_question, state.get("city", "None"), state.get("interests", "None"), budget)
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
    enriched_question = state["question"]
    hotel_preferences = [
        state.get("breakfast", "None"),
        state.get("amenities", "None"),
    ]
    preference_text = ", ".join([p for p in hotel_preferences if p and p != "None"])
    if preference_text:
        enriched_question = f"{enriched_question}. Preferences: {preference_text}"

    checkin = state.get("checkin")
    checkout = state.get("checkout")
    if checkin == "None": checkin = None
    if checkout == "None": checkout = None

    answer = hotel_agent(
        enriched_question,
        state.get("city", "None"),
        state.get("budget", "None"),
        state.get("guests", state.get("travelers", 1)),
        checkin=checkin,
        checkout=checkout,
        rooms=state.get("rooms", 1),
        amenities=state.get("amenities", "None"),
        breakfast=state.get("breakfast", "None")
    )
    
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
    interests = state.get("interests", "None")
    attraction_preferences = [
        state.get("max_distance", "None"),
        state.get("price_preference", "None"),
        state.get("traveler_type", "None"),
    ]
    extra = ", ".join([p for p in attraction_preferences if p and p != "None"])
    if extra:
        interests = f"{interests}, {extra}" if interests != "None" else extra

    answer = nearby_agent(state["question"], state.get("city", "None"), interests)
    text = answer.get("answer") if isinstance(answer, dict) else answer
    source = answer.get("source", "Groq") if isinstance(answer, dict) else "Groq"
    data = answer.get("data", []) if isinstance(answer, dict) else []

    return {
        "responses": [
            f"Nearby Places to visit:\n{text}\n[SOURCE:{source}]"
        ],
        "nearby_data": data
    }


def budget_node(state):
    answer = budget_agent(
        state["question"],
        city=state.get("city", "None"),
        days=state.get("days", 3),
        travelers=state.get("travelers", 1),
        budget_level=state.get("budget", "Moderate"),
        include_hotel=state.get("include_hotel", "Yes"),
        include_transport=state.get("include_transport", "Yes"),
        shopping_budget=state.get("shopping_budget", "Yes"),
    )
    text = answer.get("answer") if isinstance(answer, dict) else str(answer)
    data = answer.get("data", {}) if isinstance(answer, dict) else {}

    return {
        "responses": [
            f"Budget:\n{text}\n[SOURCE:{answer.get('source', 'budget_service') if isinstance(answer, dict) else 'budget_service'}]"
        ],
        "budget_data": data
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
    "budget",
    budget_node
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
builder.add_node("voice_notification", generate_voice_notifications)

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
    "budget",
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
    return "voice_notification"

builder.add_conditional_edges(
    "merge",
    merge_router,
    {
        "calendar_preview": "calendar_preview",
        "voice_notification": "voice_notification",
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

builder.add_edge("calendar_preview", "voice_notification")
builder.add_edge("save_itinerary", "voice_notification")
builder.add_edge("google_calendar", "voice_notification")
builder.add_edge("delete_itinerary", "voice_notification")
builder.add_edge("modify_itinerary", "calendar_preview")
builder.add_edge("voice_notification", END)

graph = builder.compile()
