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
    clean_val,
    route_for_agent,
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
from agents.crowd_agent import crowd_agent
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


def demo_log(step: str, message: str) -> None:
    print(f"[LOG][{step}] {message}")


def demo_names(items, name_key: str = "name", limit: int = 3) -> str:
    if not items:
        return "none"
    names = []
    for item in items[:limit]:
        if isinstance(item, dict):
            names.append(str(item.get(name_key) or item.get("title") or item.get("activity") or "Unnamed"))
    return ", ".join(names) if names else "none"


def cache_agent_data(key: str, data) -> None:
    if not data:
        return
    try:
        import json
        update_guided_state(key, json.dumps(data))
    except Exception as exc:
        demo_log("AGENT_CACHE", f"save_failed key={key}, reason={exc}")


def supervisor_node(state):

    # Route first to update database state
    routes = route_question(state)
    g_state = get_guided_state()
    demo_log(
        "GRAPH_SUPERVISOR",
        f"initial_routes={routes}, city={state.get('city', 'None')}, destination={state.get('destination', 'None')}, active_agent={g_state.get('active_agent', '') or 'none'}"
    )
    active_agent, missing_key, missing_prompt = get_active_agent_question(g_state)
    if active_agent and missing_key and len(routes) <= 1:
        demo_log("GRAPH_SUPERVISOR", f"prompting_active_agent={active_agent}, missing={missing_key}, routes=['merge']")
        return {
            **state,
            "answer": missing_prompt,
            "routes": ["merge"]
        }
    completed_agent = g_state.get("last_completed_agent")
    if completed_agent and routes and routes != ["weather"] and routes != ["transport"] and not ("weather" in routes and len(routes) == 1):
        agent_context = get_agent_context(completed_agent, g_state)
        update_guided_state("last_completed_agent", "")
        demo_log("GRAPH_SUPERVISOR", f"completed_agent={completed_agent}, rebuilding_context=yes")
        city = clean_val(agent_context.get("destination")) or clean_val(agent_context.get("city")) or clean_val(g_state.get("destination")) or clean_val(g_state.get("city")) or clean_val(state.get("destination")) or clean_val(state.get("city")) or "Trichy"
        update_guided_state("destination", city)
        update_guided_state("city", city)
        budget = clean_val(agent_context.get("budget")) or clean_val(agent_context.get("budget_level")) or clean_val(g_state.get("budget")) or clean_val(state.get("budget")) or "Moderate"
        interests = clean_val(agent_context.get("interests")) or clean_val(g_state.get("interests")) or clean_val(state.get("interests")) or "Any"
        days = clean_val(agent_context.get("days")) or clean_val(g_state.get("days")) or clean_val(state.get("days")) or 3
        travelers = clean_val(agent_context.get("travelers")) or clean_val(agent_context.get("guests")) or clean_val(g_state.get("travelers")) or clean_val(state.get("travelers")) or 1
        travel_mode = clean_val(agent_context.get("travel_mode")) or clean_val(g_state.get("travel_mode")) or clean_val(state.get("travel_mode")) or "Car"
        try:
            days = int(days)
        except Exception:
            days = 3
        try:
            travelers = int(travelers)
        except Exception:
            travelers = 1

        from datetime import datetime, timedelta
        travel_date = clean_val(agent_context.get("travel_date")) or clean_val(g_state.get("travel_date")) or clean_val(state.get("travel_date")) or (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        question = state.get("question")
        if completed_agent == "calendar":
            travel_style = clean_val(agent_context.get("travel_style")) or clean_val(g_state.get("travel_style")) or clean_val(state.get("travel_style")) or "Cultural"
            question = (
                f"Plan a {days}-day trip to {city} starting on {travel_date} by {travel_mode}. "
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


        final_state = {
            **state,
            "question": question,
            "city": city,
            "destination": agent_context.get("destination", city),
            "days": days,
            "budget": budget,
            "travelers": travelers,
            "travel_style": agent_context.get("travel_style", state.get("travel_style", "None")),
            "interests": interests,
            "travel_date": travel_date,
            "current_location": g_state.get("current_location", "Chennai"),
            "travel_mode": state.get("travel_mode") or g_state.get("travel_mode", "Car"),
            "checkin": agent_context.get("checkin", "None"),
            "checkout": agent_context.get("checkout", "None"),
            "guests": agent_context.get("guests") or travelers,
            "breakfast": agent_context.get("breakfast", "None"),
            "hotel_type": agent_context.get("hotel_type", "None"),
            "amenities": agent_context.get("amenities", "None"),
            "budget_per_person": agent_context.get("budget_per_person", "None"),
            "diet": agent_context.get("diet", "None"),
            "cuisine": agent_context.get("cuisine", "None"),
            "meal_time": agent_context.get("meal_time", "None"), # Added
            "family_friendly": agent_context.get("family_friendly", "None"),
            "outdoor_seating": agent_context.get("outdoor_seating", "None"),
            "allergies": agent_context.get("allergies", "None"),
            "max_distance": agent_context.get("max_distance", "None"),
            "price_preference": agent_context.get("price_preference", "None"),
            "traveler_type": agent_context.get("traveler_type", "None"), # Added
            "include_hotel": agent_context.get("include_hotel", "Yes"),
            "include_transport": agent_context.get("include_transport", "Yes"),
            "shopping_budget": agent_context.get("shopping_budget", "Yes"),
            "travel_date": travel_date,
            "current_location": agent_context.get("current_location", "None"),
            "travel_mode": agent_context.get("travel_mode", "None"),
            "routes": routes
        }
        demo_log(
            "GRAPH_SUPERVISOR",
            f"completed_context_routes={routes}, city={final_state.get('city')}, days={final_state.get('days')}, mode={final_state.get('travel_mode')}"
        )
        return final_state
    
    # Direct routing for active preview lifecycle actions
    lifecycle_actions = ["save_itinerary", "google_calendar", "modify_itinerary", "regenerate_itinerary", "delete_itinerary"]
    if len(routes) == 1 and routes[0] in lifecycle_actions:
        demo_log("GRAPH_SUPERVISOR", f"lifecycle_action={routes[0]}, routes={routes}")
        return {
            **state,
            "routes": routes
        }

    is_active = g_state.get("is_active") == "1" and len(routes) <= 1
    
    if is_active or routes == ["merge"]:
        missing_key, missing_prompt = get_next_missing_field(g_state)
        demo_log("GRAPH_SUPERVISOR", f"guided_prompt=yes, missing={missing_key}, routes=['merge']")
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
        from supervisor import extract_all_opening_details
        extracted = extract_all_opening_details(state["question"])
        
        st_dest = clean_val(state.get("destination")) or clean_val(state.get("city"))
        st_loc = clean_val(state.get("current_location"))
        st_date = clean_val(state.get("travel_date"))
        st_days = clean_val(state.get("days"))
        st_budget = clean_val(state.get("budget"))
        st_travelers = clean_val(state.get("travelers"))
        st_style = clean_val(state.get("travel_style"))
        st_mode = clean_val(state.get("travel_mode"))
        st_interests = clean_val(state.get("interests"))

        destination = clean_val(g_state.get("destination")) or clean_val(extracted.get("destination")) or st_dest or "Salem"
        current_loc = clean_val(g_state.get("current_location")) or clean_val(extracted.get("current_location")) or st_loc or "Chennai"
        travel_date = clean_val(g_state.get("travel_date")) or clean_val(extracted.get("travel_date")) or st_date or (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        days_val = clean_val(g_state.get("days")) or clean_val(extracted.get("days")) or st_days or "3"
        try:
            days = int(days_val)
        except Exception:
            days = 3
            
        budget = clean_val(g_state.get("budget")) or clean_val(extracted.get("budget")) or st_budget or "Moderate"
        
        travelers_val = clean_val(g_state.get("travelers")) or clean_val(extracted.get("travelers")) or st_travelers or "1"
        try:
            travelers = int(travelers_val)
        except Exception:
            travelers = 1
            
        travel_style = clean_val(g_state.get("travel_style")) or clean_val(extracted.get("travel_style")) or st_style or "Cultural"
        travel_mode = clean_val(g_state.get("travel_mode")) or clean_val(extracted.get("travel_mode")) or st_mode or "Car"
        interests = clean_val(g_state.get("interests")) or clean_val(extracted.get("interests")) or st_interests or "Any"
        
        # Persist extracted values into guided state for session consistency
        update_guided_state("destination", destination)
        update_guided_state("current_location", current_loc)
        update_guided_state("travel_date", travel_date)
        update_guided_state("days", str(days))
        update_guided_state("budget", budget)
        update_guided_state("travel_style", travel_style)
        update_guided_state("travel_mode", travel_mode)

        compiled_question = (
            f"Plan a {days}-day trip to {destination} starting on {travel_date} by {travel_mode}. "
            f"Travel style is {travel_style}, travelers is {travelers}, budget is {budget}, interests are {interests}."
        )
        final_state = {
            **state,
            "question": compiled_question,
            "city": destination,
            "destination": destination,
            "days": days,
            "budget": budget,
            "travelers": travelers,
            "travel_style": travel_style,
            "interests": interests,
            "travel_date": travel_date,
            "current_location": current_loc,
            "travel_mode": travel_mode,
            "routes": routes
        }
        demo_log(
            "GRAPH_SUPERVISOR",
            f"multi_agent_calendar_context city={destination}, days={days}, mode={travel_mode}, routes={routes}"
        )
        return final_state

    details = extract_query_details(state["question"])
    stateless_routes = route_question(state)
    demo_log("GRAPH_SUPERVISOR", f"stateless_routes={stateless_routes}, extracted_city={details.get('city', 'None')}")
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
    question = state["question"]
    city = state.get("city", "None")
    budget = clean_val(state.get("budget_per_person")) or clean_val(state.get("budget")) or "None"
    cuisine = state.get("cuisine", "None")
    diet = state.get("diet", "None")
    meal_time = state.get("meal_time", "None")
    family_friendly = state.get("family_friendly", "None")
    outdoor_seating = state.get("outdoor_seating", "None")
    allergies = state.get("allergies", "None")

    # The supervisor already builds a good question, but we can pass structured data too
    answer = restaurant_agent(
        question=question,
        city=city,
        interests=state.get("interests", "None"), # Interests can be cuisine
        budget=budget,
        cuisine=cuisine,
        diet=diet,
        meal_time=meal_time,
        family_friendly=family_friendly,
        outdoor_seating=outdoor_seating,
        allergies=allergies
    )
    text = answer.get("answer") if isinstance(answer, dict) else answer
    source = answer.get("source", "Groq") if isinstance(answer, dict) else "Groq"
    data = answer.get("data", []) if isinstance(answer, dict) else []
    demo_log(
        "RESTAURANT_AGENT",
        f"city={city}, budget={budget}, cuisine={cuisine}, diet={diet}, source={source}, count={len(data)}, sample={demo_names(data)}"
    )
    cache_agent_data("restaurants_data", data)

    return {
        "responses": [
            f"Restaurant suggestions:\n{text}\n[SOURCE:{source}]"
        ],
        "restaurants_data": data
    }


def hotel_node(state):
    checkin = state.get("checkin")
    checkout = state.get("checkout")
    if checkin == "None": checkin = None
    if checkout == "None": checkout = None

    answer = hotel_agent(
        question=state["question"],
        city=state.get("city", "None"),
        budget=state.get("budget", "None"),
        travelers=state.get("guests", state.get("travelers", 1)),
        checkin=checkin,
        checkout=checkout,
        rooms=state.get("rooms", 1),
        breakfast=state.get("breakfast", "None"),
        hotel_type=state.get("hotel_type", "None"),
        amenities=state.get("amenities", "None")
    )
    
    if isinstance(answer, dict):
        text = answer.get("hotels") or answer.get("answer") or answer.get("message", "Could not retrieve hotel info.")
        source = answer.get("source", "Groq")
        data = answer.get("data", [])
    else:
        text = str(answer)
        source = "Groq"
        data = []
    demo_log(
        "HOTEL_AGENT",
        f"city={state.get('city', 'None')}, budget={state.get('budget', 'None')}, source={source}, count={len(data)}, sample={demo_names(data)}"
    )
    cache_agent_data("hotels_data", data)

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
    # Discovery queries return a structured payload used by the frontend to
    # render image cards. Keep it in graph state instead of reducing it to
    # the summary text above.
    nearby_result = answer.get("nearbyResult") if isinstance(answer, dict) else None
    demo_log(
        "NEARBY_AGENT",
        f"city={state.get('city', 'None')}, interests={interests}, source={source}, count={len(data)}, sample={demo_names(data)}"
    )
    cache_agent_data("nearby_data", data)

    return {
        "responses": [
            f"Nearby Places to visit:\n{text}\n[SOURCE:{source}]"
        ],
        "nearby_data": data,
        "nearbyResult": nearby_result,
    }


def budget_node(state):
    demo_log(
        "BUDGET_AGENT_START",
        f"city={state.get('city', 'None')}, days={state.get('days', 3)}, budget={state.get('budget', 'Moderate')}, travelers={state.get('travelers', 1)}"
    )
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
    demo_log(
        "BUDGET_AGENT",
        f"source={answer.get('source', 'budget_service') if isinstance(answer, dict) else 'budget_service'}, has_data={'yes' if data else 'no'}"
    )

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
    weather_summary = data if data else str(text)[:160].replace("\n", " ")
    demo_log("WEATHER_AGENT", f"city={state.get('city', 'None')}, data={weather_summary}")

    return {
        "responses": [
            f"Weather:\n{text}"
        ],
        "weather_data": data
    }


def general_node(state):
    demo_log("GENERAL_AGENT_START", f"question={state.get('question', '')[:120]!r}")
    answer = general_agent(state)
    demo_log("GENERAL_AGENT", f"source={answer.get('source', 'Groq') if isinstance(answer, dict) else 'Groq'}")

    return {
        "responses": [
            f"{answer.get('answer')}\n[SOURCE:{answer.get('source', 'Groq')}]"
        ]
    }


def transport_node(state):
    import re
    import json
    from supervisor import get_guided_state, update_guided_state, clean_val, extract_query_details, extract_all_opening_details

    g_state = get_guided_state()
    current_loc = clean_val(state.get("current_location")) or clean_val(g_state.get("current_location"))
    dest_city = clean_val(state.get("destination")) or clean_val(state.get("city")) or clean_val(g_state.get("destination")) or clean_val(g_state.get("city")) or "Bangalore"
    t_date = clean_val(state.get("travel_date")) or clean_val(g_state.get("travel_date"))

    def is_coords(s: str) -> bool:
        if not s: return True
        return bool(re.search(r'^\s*[-+]?\d+(?:\.\d+)?\s*,\s*[-+]?\d+(?:\.\d+)?\s*$', str(s)))

    source_city = current_loc if (current_loc and not is_coords(current_loc)) else None
    destination_city = dest_city

    # Check question for "from X to Y"
    q_text = state.get("question", "")
    match = re.search(r'from\s+([A-Za-z\s]{2,20})\s+to\s+([A-Za-z\s]{2,20})', q_text, re.IGNORECASE)
    if match:
        s_extracted = match.group(1).strip().title()
        d_extracted = match.group(2).strip().title()
        if s_extracted and not is_coords(s_extracted) and s_extracted.lower() not in {"plan", "trip", "days", "day", "a"}:
            source_city = s_extracted
        if d_extracted and not is_coords(d_extracted) and d_extracted.lower() not in {"plan", "trip", "days", "day", "a"}:
            destination_city = d_extracted

    if not source_city or "Plan" in str(source_city):
        details = extract_query_details(q_text)
        if details:
            extracted_src = clean_val(details.get("current_location")) or clean_val(details.get("city"))
            if extracted_src and not is_coords(extracted_src) and extracted_src.lower() != destination_city.lower():
                source_city = extracted_src
            if not t_date:
                t_date = clean_val(details.get("travel_date"))

    # Ensure source_city is valid and NOT equal to destination_city
    if not source_city or is_coords(source_city) or source_city.lower() == destination_city.lower():
        if destination_city.lower() in {"chennai", "madras"}:
            source_city = "Bangalore"
        else:
            source_city = "Chennai"

    if not t_date or t_date.lower() in {"none", "null"}:
        from datetime import datetime, timedelta
        t_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    travel_date = t_date

    t_mode = clean_val(state.get("travel_mode")) or clean_val(g_state.get("travel_mode"))
    if not t_mode or t_mode.lower() in {"none", "null"}:
        extracted = extract_all_opening_details(q_text)
        t_mode = clean_val(extracted.get("travel_mode"))
    if not t_mode or t_mode.lower() in {"none", "null"}:
        t_mode = "Flight"

    print(f"[TRANSPORT NODE] Source: {source_city}, Destination: {destination_city}, Date: {travel_date}, Mode: {t_mode}")

    answer = transport_agent(
        q_text,
        source=source_city,
        destination=destination_city,
        date=travel_date,
        preferred_mode=t_mode
    )

    text = answer.get("answer") if isinstance(answer, dict) else str(answer)
    source = answer.get("source", "transport_api") if isinstance(answer, dict) else "Groq"
    tickets = answer.get("tickets", []) if isinstance(answer, dict) else []
    status_obj = {
        "status": answer.get("status", "success") if isinstance(answer, dict) else "success",
        "reason": answer.get("reason", "") if isinstance(answer, dict) else ""
    }

    # Persist in guided state
    update_guided_state("transport_data", json.dumps(tickets))
    update_guided_state("transport_status", json.dumps(status_obj))

    demo_log(
        "TRANSPORT_AGENT",
        f"from={source_city}, to={destination_city}, date={travel_date}, mode={t_mode}, source={source}, count={len(tickets)}"
    )

    return {
        "responses": [
            f"Transport options:\n{text}\n[SOURCE:{source}]"
        ],
        "transport_data": tickets,
        "transport_status": status_obj
    }

def crowd_node(state):
    res = crowd_agent(state)
    crowd_info = res.get("crowd_data", {})
    return {
        "responses": [
            f"Crowd Intelligence:\n{crowd_info.get('summary', '')}"
        ],
        "crowd_data": crowd_info
    }

def calendar_node(state):
    demo_log(
        "CALENDAR_NODE_START",
        (
            f"city={state.get('city', 'None')}, days={state.get('days', 3)}, "
            f"hotels={len(state.get('hotels_data') or [])}, restaurants={len(state.get('restaurants_data') or [])}, "
            f"attractions={len(state.get('nearby_data') or [])}, transport={len(state.get('transport_data') or [])}"
        )
    )
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
        weather_data=state.get("weather_data"),
        transport_data=state.get("transport_data")
    )

    return {
        "responses": [
            f"Calendar:\n{answer}"
        ]
    }


def merge_node(state):
    if not state.get("transport_data") and str(state.get("include_transport", "Yes")).lower() != "no":
        q_lower = str(state.get("question", "")).lower()
        is_itinerary_request = any(k in q_lower for k in ["trip", "plan", "itinerary", "vacation", "holiday", "tour"])
        destination_city = clean_val(state.get("destination")) or clean_val(state.get("city"))
        source_city = clean_val(state.get("current_location"))
        travel_mode = clean_val(state.get("travel_mode")) or clean_val(get_guided_state().get("travel_mode")) or "Flight"
        travel_date = clean_val(state.get("travel_date")) or clean_val(get_guided_state().get("travel_date"))

        if is_itinerary_request and destination_city and source_city and travel_mode:
            if not travel_date or travel_date.lower() in {"none", "null"}:
                from datetime import datetime, timedelta
                travel_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            try:
                transport_result = transport_agent(
                    state.get("question", ""),
                    source=source_city,
                    destination=destination_city,
                    date=travel_date,
                    preferred_mode=travel_mode
                )
                tickets = transport_result.get("tickets", []) if isinstance(transport_result, dict) else []
                status_obj = {
                    "status": transport_result.get("status", "success") if isinstance(transport_result, dict) else "success",
                    "reason": transport_result.get("reason", "") if isinstance(transport_result, dict) else ""
                }
                if tickets:
                    state["transport_data"] = tickets
                    state["transport_status"] = status_obj
                    import json
                    update_guided_state("transport_data", json.dumps(tickets))
                    update_guided_state("transport_status", json.dumps(status_obj))
                demo_log(
                    "TRANSPORT_AGENT",
                    f"merge_fallback=yes, from={source_city}, to={destination_city}, date={travel_date}, mode={travel_mode}, count={len(tickets)}"
                )
            except Exception as exc:
                demo_log("TRANSPORT_AGENT", f"merge_fallback=failed, reason={exc}")

    h_data = state.get('hotels_data') or []
    r_data = state.get('restaurants_data') or []
    n_data = state.get('nearby_data') or []
    if h_data or r_data or n_data:
        print(f"[DEBUG] Merge Node compiled: {len(h_data)} hotels, {len(r_data)} restaurants, {len(n_data)} attractions")
    demo_log(
        "MERGE_INPUTS",
        (
            f"hotels={len(h_data)} [{demo_names(h_data)}]; "
            f"restaurants={len(r_data)} [{demo_names(r_data)}]; "
            f"attractions={len(n_data)} [{demo_names(n_data)}]; "
            f"weather={'yes' if state.get('weather_data') else 'no'}; "
            f"transport={len(state.get('transport_data') or [])}"
        )
    )

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
        other_agent_info=other_agent_info,
        transport_data=state.get("transport_data")
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
    demo_log(
        "CALENDAR_OUTPUT",
        f"items={len(calendar_items)}, days={days}, sample={demo_names(calendar_items, name_key='activity', limit=5)}"
    )

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
        "routes": ["calendar_preview"],
        "hotels_data": state.get("hotels_data"),
        "restaurants_data": state.get("restaurants_data"),
        "nearby_data": state.get("nearby_data"),
        "nearbyResult": state.get("nearbyResult"),
        "transport_data": state.get("transport_data"),
        "transport_status": state.get("transport_status")
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
    "transport",
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

VALID_GRAPH_NODES = {
    "restaurant", "hotel", "nearby", "budget", "transport", "weather", "crowd", "general",
    "save_itinerary", "google_calendar", "modify_itinerary", "regenerate_itinerary", "delete_itinerary"
}

def router(state):
    sends = []
    seen = set()

    for route in state.get("routes", []):
        normalized = route_for_agent(route)
        if normalized in {"calendar", "calendar_preview"}:
            for dependency in ["hotel", "restaurant", "nearby", "weather", "transport"]:
                if dependency in VALID_GRAPH_NODES and dependency not in seen:
                    seen.add(dependency)
                    sends.append(Send(dependency, state))
            continue
        if normalized in VALID_GRAPH_NODES and normalized not in seen:
            seen.add(normalized)
            sends.append(Send(normalized, state))

    demo_log(
        "GRAPH_ROUTER",
        f"routes={state.get('routes', [])}, dispatched={[getattr(send, 'node', str(send)) for send in sends]}"
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
    "transport",
    "merge"
)


builder.add_edge(
    "weather",
    "merge"
)

builder.add_node(
    "crowd",
    crowd_node
)

builder.add_edge(
    "crowd",
    "merge"
)


builder.add_edge(
    "general",
    "merge"
)




def merge_router(state):
    g_state = get_guided_state()
    routes = state.get("routes", [])
    if "calendar" in routes or "calendar_preview" in routes:
        demo_log("MERGE_ROUTER", f"routes={routes}, next=calendar_preview")
        return "calendar_preview"
    demo_log("MERGE_ROUTER", f"routes={routes}, next=voice_notification")
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
    demo_log("REGENERATE_ROUTER", f"routes={state.get('routes', [])}, dispatched={[getattr(send, 'node', str(send)) for send in sends]}")
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
