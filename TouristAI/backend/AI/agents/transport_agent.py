import os
import sys
import json
import asyncio
from datetime import datetime

# Adjust path to import correctly from transport
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transport.models import TransportRequest
from transport.transport_service import TransportService
from supervisor import get_guided_state, update_guided_state

def run_async(coro):
    """Synchronous wrapper to execute coroutines safely in a separate loop."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If running in uvicorn thread, run in a separate thread loop
            import threading
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(lambda: asyncio.run(coro))
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

def transport_agent(question: str,
                    source: str = "None",
                    destination: str = "None",
                    date: str = "None",
                    preferred_mode: str = "None") -> dict:
    """
    Refactored TransportAgent that classifies transport requests, invokes 
    the TransportService to scrape/normalize/score options, and returns 
    the best ticket choices.
    """
    print(f"[TransportAgent] Query: '{question}' from '{source}' to '{destination}' on '{date}' (Preferred Mode: '{preferred_mode}')")

    if source == "None" or destination == "None":
        return {
            "source": "transport_agent",
            "answer": "Please specify both origin and destination cities to search for transport tickets."
        }

    # Format date: default to 15 days ahead if none specified
    if not date or date == "None":
        from datetime import timedelta
        date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")

    # 1. Classify modes based on explicit parameter, keyword detection & guided state
    question_lower = question.lower()
    g_state = get_guided_state()
    state_mode = (preferred_mode if preferred_mode != "None" else (g_state.get("calendar.travel_mode") or g_state.get("travel_mode") or "None")).strip().title()

    sel_mode = None
    if preferred_mode and preferred_mode != "None" and preferred_mode != "":
        sm_lower = preferred_mode.lower()
        if any(k in sm_lower for k in ["car", "cab", "taxi", "drive", "self-drive"]):
            sel_mode = "Car"
        elif any(k in sm_lower for k in ["bus", "redbus"]):
            sel_mode = "Bus"
        elif any(k in sm_lower for k in ["train", "rail"]):
            sel_mode = "Train"
        elif any(k in sm_lower for k in ["flight", "plane", "fly", "air"]):
            sel_mode = "Flight"
        else:
            sel_mode = preferred_mode.title()

    if not sel_mode:
        if any(k in question_lower for k in ["car", "cab", "taxi", "drive", "self-drive"]):
            sel_mode = "Car"
        elif any(k in question_lower for k in ["bus", "redbus"]):
            sel_mode = "Bus"
        elif any(k in question_lower for k in ["train", "rail", "irctc"]):
            sel_mode = "Train"
        elif any(k in question_lower for k in ["flight", "plane", "fly", "air"]):
            sel_mode = "Flight"

    if not sel_mode and state_mode != "None" and state_mode != "":
        sel_mode = state_mode

    # Default to Car if unspecified
    if not sel_mode:
        sel_mode = "Car"

    # If user explicitly specified a mode (e.g. Flight, Car, Bus, Train):
    # search ONLY that selected mode first to prevent unnecessary scraper calls & ticket pollution.
    if sel_mode and sel_mode != "Any" and sel_mode != "None":
        modes = [sel_mode]
    else:
        modes = ["Car", "Bus", "Train", "Flight"]

    # 2. Extract preferences and budget from guided state
    budget_val = g_state.get("budget", "None")
    budget_limit = None
    if budget_val != "None":
        try:
            budget_limit = float(budget_val)
        except ValueError:
            b_lower = budget_val.lower()
            if "low" in b_lower:
                budget_limit = 2000.0
            elif "moderate" in b_lower:
                budget_limit = 6000.0
            elif "luxury" in b_lower or "high" in b_lower:
                budget_limit = 25000.0

    travelers_val = 1
    try:
        travelers_val = int(g_state.get("travelers", 1))
    except ValueError:
        pass

    # Extract time convenience preferences from question (e.g. morning, evening)
    time_pref = None
    for t_pref in ["morning", "afternoon", "evening", "night"]:
        if t_pref in question_lower:
            time_pref = t_pref.capitalize()
            break

    # 3. Create request payload using the resolved preferred_mode
    req = TransportRequest(
        from_city=source,
        to_city=destination,
        date=date,
        modes=modes,
        budget=budget_limit,
        travelers=travelers_val,
        time_preference=time_pref,
        preferred_mode=sel_mode
    )

    # 4. Invoke TransportService asynchronously
    service = TransportService()
    print(f"[TransportAgent] Invoking TransportService for modes {modes} with budget {budget_limit}")
    result = run_async(service.search_transport(req))

    tickets = result.get("tickets", [])
    status = result.get("status", "success")
    reason = result.get("reason", "")

    # 5. Format text answer for LLM / chat context
    if status == "success" and tickets:
        formatted_lines = []
        if preferred_mode == "Car":
            formatted_lines.append(f"🚗 **Personal / Self-Drive Car Selected**: No public transit booking ticket is required if traveling by personal vehicle. Outstation cab and self-drive rental options from {source} to {destination} on {date} are listed below:\n")
        else:
            formatted_lines.append(f"Found the top {len(tickets)} transport options from {source} to {destination} on {date}:\n")
        
        for idx, ticket in enumerate(tickets, 1):
            formatted_lines.append(f"{idx}. **[{ticket['mode']}] {ticket['carrier']}** - {ticket['vehicle_type']}")
            formatted_lines.append(f"   - ⏰ Departs: {ticket['departure']} | Arrives: {ticket['arrival']} | Duration: {ticket['duration']}")
            formatted_lines.append(f"   - 💰 Price: ₹{ticket['price']:,} INR | Rating: ⭐ {ticket['rating']} | Score: {ticket['score']}/100")
            formatted_lines.append(f"   - 🔗 [Book on {ticket['booking_source']}]({ticket['booking_url']})")
            formatted_lines.append("")
        answer = "\n".join(formatted_lines)
    else:
        answer = f"⚠️ Could not find live transport options. Reason: {reason or 'No available schedules matches filters.'}"

    # Stash the parsed tickets and status inside PostgreSQL guided state for the merge node
    update_guided_state("transport_data", json.dumps(tickets))
    update_guided_state("transport_status", json.dumps({
        "status": status,
        "reason": reason,
        "last_updated": result.get("last_updated", datetime.now().isoformat())
    }))

    return {
        "source": "transport_agent",
        "answer": answer,
        "tickets": tickets,
        "status": status,
        "reason": reason
    }