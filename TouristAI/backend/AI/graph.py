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
from rag_service import client



builder = StateGraph(AgentState)


def supervisor_node(state):
    g_state = get_guided_state()
    
    # Check if we are waiting for a save confirmation
    if g_state.get("awaiting_save_confirmation") == "1":
        from supervisor import update_guided_state, save_itinerary_to_db
        update_guided_state("awaiting_save_confirmation", "0")
        
        question_lower = state["question"].strip().lower()
        
        # Check if the user confirmed
        if any(yes_kw in question_lower for yes_kw in ["yes", "yeah", "sure", "ok", "save", "yep", "please"]):
            last_itinerary = g_state.get("last_itinerary", "")
            if last_itinerary:
                res = save_itinerary_to_db(last_itinerary)
                if res.get("success"):
                    msg = (
                        f"✅ **Itinerary Saved Successfully!**\n\n"
                        f"I have saved the activities for '{res.get('trip_name')}' to your local database. "
                        f"You can now download the `.ics` calendar file from the menu options to sync it with Google Calendar or Apple Calendar!"
                    )
                else:
                    msg = f"❌ **Error Saving Itinerary:** {res.get('message')}"
            else:
                msg = "I couldn't find the last generated itinerary to save. Please request a new trip plan first."
                
            return {
                **state,
                "answer": msg,
                "responses": [],
                "routes": ["merge"]
            }
            
        elif any(no_kw in question_lower for no_kw in ["no", "nope", "don't", "cancel", "nay"]):
            return {
                **state,
                "answer": "No problem! I won't save this itinerary. Let me know if you want to plan another trip or need any other details.",
                "responses": [],
                "routes": ["merge"]
            }
        else:
            # Clear flag and fall through to normal execution
            pass

    # Route first to update database state
    routes = route_question(state)
    
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

    return {
        "responses": [
            f"Restaurant suggestions:\n{text}\n[SOURCE:{source}]"
        ]
    }


def hotel_node(state):
    answer = hotel_agent(state["question"], state.get("city", "None"), state.get("budget", "None"), state.get("travelers", 1))
    
    # The hotel_agent returns a dictionary with different keys based on the source.
    # We need to extract the relevant text from 'hotels' or 'answer'.
    if isinstance(answer, dict):
        text = answer.get("hotels") or answer.get("answer") or answer.get("message", "Could not retrieve hotel info.")
        source = answer.get("source", "Groq")
    else:
        text = str(answer)
        source = "Groq"

    return {
        "responses": [
            f"Hotel suggestions:\n{text}\n[SOURCE:{source}]"
        ]
    }


def nearby_node(state):
    answer = nearby_agent(state["question"], state.get("city", "None"), state.get("interests", "None"))
    text = answer.get("answer") if isinstance(answer, dict) else answer
    source = answer.get("source", "Groq") if isinstance(answer, dict) else "Groq"

    return {
        "responses": [
            f"Nearby Places to visit:\n{text}\n[SOURCE:{source}]"
        ]
    }


def weather_node(state):
    answer = weather_agent(state["question"], state.get("city", "None"))

    # Weather agent response is a string with source info already inside
    return {
        "responses": [
            f"Weather:\n{answer}"
        ]
    }


def general_node(state):
    answer = general_agent(state)

    # General agent now returns a dict with 'answer' and 'source'
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
        state["question"],
        state.get("city", "None"),
        state.get("days", 3),
        state.get("interests", "None"),
        state.get("travel_style", "None"),
        state.get("budget", "None")
    )

    return {
        "responses": [
            f"Calendar:\n{answer}"
        ]
    }


def merge_node(state):
    # If there is only one response, we can return it directly to save time.
    # This ensures general queries or individual agent warnings are returned directly.
    if len(state["responses"]) <= 1:
        context = "\n\n".join(state["responses"])
        if not context.strip():
            return {
                "answer": state.get("answer", "")
            }
        return {
            "answer": context
        }

    # If the destination city is not specified and multiple agents ran, politely ask the user to specify it
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

    # Combine the responses into a context
    context = "\n\n".join(state["responses"])
        
    prompt = (
        "You are a highly professional, friendly, and structured AI travel guide.\n"
        "A traveler requested a trip plan, and our sub-agents gathered the following raw details:\n\n"
        f"{context}\n\n"
        "Please compile, personalize, and synthesize this information into a clean, concise, and structured itinerary guide.\n"
        "Follow these rules strictly:\n"
        "1. Start with the title: 📍 [City Name]\n"
        "2. Directly below the title, provide a personalized introduction of exactly 2 sentences, incorporating their details:\n"
        f"   - Sentence 1: \"Great! I've planned a {state.get('days', 3)}-day {budget_description} {state.get('city', 'None').title()} trip for {state.get('travelers', 1)} traveler(s) (style: {state.get('travel_style', 'None')}) who enjoy {state.get('interests', 'None')}.\"\n"
        f"   - Sentence 2: \"This itinerary focuses on {state.get('interests', 'None')} attractions, budget-appropriate stays, and local dining while keeping your total budget {budget_limit_text}.\"\n"
        "3. Keep the responses concise and actionable. Avoid long generic travel articles. Use markdown structure.\n"
        "4. Incorporate the following sections in order, using these EXACT section titles (with emojis):\n"
        "   🌤 **Weather** (Concise summary of temperature and packing/sightseeing advice)\n"
        "   🏨 **Hotels** (List of budget-appropriate hotels recommended by the sub-agent)\n"
        "   🍽 **Restaurants** (List of dining options recommended by the sub-agent)\n"
        "   🗺 **Attractions** (List of sightseeing options matching traveler interests)\n"
        "   🗓 **Day 1** (Day 1 activities)\n"
        "   [For multiple days, add 🗓 **Day 2**, etc. in sequence]\n"
        f"   💰 **Estimated Budget** (Show a simple cost breakdown. The total sum of stays, food, and activities "
        f"MUST strictly respect the budget category: if 'Budget', the total sum must be under ₹5,000; "
        f"if 'Moderate', between ₹5,000 and ₹15,000; if 'Luxury', above ₹15,000. Do not exceed these boundaries.)\n"
        "5. Under Hotels and Restaurants, ensure the individual price ranges mentioned align with the total budget (e.g. if the budget is under ₹5,000, do not list hotels that cost ₹8,000 per night).\n"
        "6. Do not include raw Python dictionaries, bracket symbols, list markers from sub-agent templates, or debug information."
    )
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        synthesis = response.choices[0].message.content.strip()
        
        from supervisor import update_guided_state
        update_guided_state("last_itinerary", synthesis)
        update_guided_state("awaiting_save_confirmation", "1")
        
        synthesis += "\n\nWould you like me to save this itinerary to your calendar? (Reply **'Yes'** to save it to your database)"
        
        return {
            "answer": synthesis
        }
    except Exception as e:
        print(f"Error in synthesis merge_node: {e}")
        from supervisor import update_guided_state
        update_guided_state("last_itinerary", context)
        update_guided_state("awaiting_save_confirmation", "1")
        
        context_with_prompt = context + "\n\nWould you like me to save this itinerary to your calendar? (Reply **'Yes'** to save it to your database)"
        return {
            "answer": context_with_prompt
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
    "calendar",
    calendar_node
)



builder.add_node(
    "merge",
    merge_node
)

builder.set_entry_point(
    "supervisor"
)

def router(state):
    sends = []

    for route in state["routes"]:
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



builder.add_edge(
    "calendar",
    "merge"
)

builder.add_edge(
    "merge",
    END
)

graph = builder.compile()