import re
import json
import os
import sqlite3
from typing import Optional
from rag_service import client
from services.questionnaire_service import (
    build_context as build_agent_questionnaire_context,
    extract_initial_values as extract_agent_initial_values,
    get_next_missing_field as get_next_missing_agent_field,
    normalize_agent,
    parse_field as parse_agent_field,
    route_for_agent,
    state_key as agent_state_key,
    save_agent_answer,
    get_progress_metadata,
)

def demo_log(step: str, message: str) -> None:
    print(f"[LOG][{step}] {message}")

def clean_val(val, default=None):
    if val is None:
        return default
    s = str(val).strip()
    if s.lower() in {"none", "null", ""}:
        return default
    return s

def get_next_missing_field(g_state: dict) -> tuple[Optional[str], Optional[str]]:
    active_agent = g_state.get("active_agent") or "calendar"
    return get_next_missing_agent_field(active_agent, g_state)

def get_active_agent_question(g_state: dict) -> tuple[Optional[str], Optional[str], Optional[str]]:
    active_agent = normalize_agent(g_state.get("active_agent", ""))
    init_guided_db()
    from database.postgres import PostgresDatabase
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM agent_sessions WHERE agent_name = %s", (active_agent,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not row or row[0] != "ACTIVE":
        return None, None, None
        
    missing_key, prompt = get_next_missing_agent_field(active_agent, g_state)
    return active_agent, missing_key, prompt

def get_agent_context(agent_name: str, g_state: dict = None) -> dict:
    g_state = g_state or get_guided_state()
    return build_agent_questionnaire_context(agent_name, g_state)

def init_guided_db():
    from database.postgres import PostgresDatabase
    PostgresDatabase.initialize()

def save_itinerary_to_db(itinerary_text: str, trip_name: str = None) -> dict:
    prompt = (
        "Analyze the following travel itinerary markdown and extract all calendar events. "
        "For each event, extract: \n"
        "1. The day number (integer, e.g. 1 for Day 1).\n"
        "2. The time slot ('Morning', 'Afternoon', or 'Evening').\n"
        "3. The time range (e.g. '9:00 AM - 12:00 PM', or default to slot times if not specified).\n"
        "4. The name of the activity/attraction.\n"
        "5. Brief details or description of the activity.\n\n"
        "Also determine a suitable unified name for this trip (e.g. 'Madurai 3-Day Tour').\n\n"
        "Return the output strictly in the following JSON format and absolutely nothing else:\n"
        "{\n"
        "  \"trip_name\": \"Name of the trip\",\n"
        "  \"events\": [\n"
        "    {\n"
        "      \"day_num\": 1,\n"
        "      \"time_slot\": \"Morning\",\n"
        "      \"time_range\": \"9:00 AM - 12:00 PM\",\n"
        "      \"activity\": \"Activity Name\",\n"
        "      \"details\": \"Activity Details\"\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Only return raw valid JSON. Do not include markdown code block syntax (like ```json).\n\n"
        f"Itinerary Markdown:\n{itinerary_text}"
    )
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        if "{" in content:
            content = content[content.find("{"):content.rfind("}")+1]
            
        data = json.loads(content)
        trip_name = trip_name or data.get("trip_name", "My Travel Trip")
        events = data.get("events", [])
        
        from database.postgres import PostgresDatabase
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM calendar_events WHERE trip_name = %s", (trip_name,))
        
        for ev in events:
            cursor.execute(
                "INSERT INTO calendar_events (trip_name, day_num, time_slot, time_range, activity, details) VALUES (%s, %s, %s, %s, %s, %s)",
                (trip_name, ev.get("day_num"), ev.get("time_slot"), ev.get("time_range"), ev.get("activity"), ev.get("details"))
            )
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Successfully saved {len(events)} events for '{trip_name}' to the database.",
            "trip_name": trip_name
        }
    except Exception as e:
        print(f"Error saving calendar events: {e}")
        return {
            "success": False,
            "message": f"Failed to save itinerary events: {str(e)}"
        }

def get_guided_state() -> dict:
    init_guided_db()
    from database.postgres import PostgresDatabase
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM guided_trip_state")
    rows = cursor.fetchall()
    state = {row[0]: row[1] for row in rows}
    
    cursor.execute("SELECT agent_name, field_name, field_value FROM agent_session_state")
    session_rows = cursor.fetchall()
    for agent, field, val in session_rows:
        state[f"{agent}.{field}"] = val
        
    cursor.close()
    conn.close()
    return state

def update_guided_state(key: str, value: str):
    init_guided_db()
    from database.postgres import PostgresDatabase
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    from datetime import datetime
    if "." in key:
        parts = key.split(".", 1)
        agent_name = parts[0]
        field_name = parts[1]
        now_str = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO agent_session_state (agent_name, field_name, field_value, updated_at) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (agent_name, field_name) DO UPDATE SET field_value = EXCLUDED.field_value, updated_at = EXCLUDED.updated_at",
            (agent_name, field_name, str(value), now_str)
        )
    else:
        cursor.execute(
            "INSERT INTO guided_trip_state (key, value) VALUES (%s, %s) "
            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
            (key, str(value))
        )
    conn.commit()
    cursor.close()
    conn.close()

def clear_guided_state():
    init_guided_db()
    from database.postgres import PostgresDatabase
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM guided_trip_state")
    cursor.execute("DELETE FROM agent_session_state")
    cursor.execute("DELETE FROM agent_sessions")
    conn.commit()
    cursor.close()
    conn.close()

def get_agent_session(agent_name: str) -> Optional[dict]:
    init_guided_db()
    from database.postgres import PostgresDatabase
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT status, last_question, next_question, completed_count, updated_at FROM agent_sessions WHERE agent_name = %s",
        (agent_name,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {
            "agent_name": agent_name,
            "status": row[0],
            "last_question": row[1],
            "next_question": row[2],
            "completed_count": row[3],
            "updated_at": row[4]
        }
    return None

def update_agent_session(agent_name: str, status: str = None, last_question: str = None, next_question: str = None, completed_count: int = None):
    init_guided_db()
    from database.postgres import PostgresDatabase
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    from datetime import datetime
    now_str = datetime.now().isoformat()
    cursor.execute("SELECT status, last_question, next_question, completed_count FROM agent_sessions WHERE agent_name = %s", (agent_name,))
    row = cursor.fetchone()
    if row:
        new_status = status if status is not None else row[0]
        new_last = last_question if last_question is not None else row[1]
        new_next = next_question if next_question is not None else row[2]
        new_completed = completed_count if completed_count is not None else row[3]
        cursor.execute(
            "UPDATE agent_sessions SET status = %s, last_question = %s, next_question = %s, completed_count = %s, updated_at = %s WHERE agent_name = %s",
            (new_status, new_last, new_next, new_completed, now_str, agent_name)
        )
    else:
        cursor.execute(
            "INSERT INTO agent_sessions (agent_name, status, last_question, next_question, completed_count, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (agent_name, status or "ACTIVE", last_question or "", next_question or "", completed_count or 0, now_str)
        )
    conn.commit()
    cursor.close()
    conn.close()

def check_session_timeout_and_commands(question: str) -> bool:
    q_clean = question.strip().lower()
    from datetime import datetime
    from database.postgres import PostgresDatabase
    if q_clean in {"cancel", "restart", "new trip"}:
        clear_guided_state()
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO agent_sessions (agent_name, status, updated_at) VALUES ('general', 'CANCELLED', %s) "
            "ON CONFLICT (agent_name) DO UPDATE SET status = EXCLUDED.status, updated_at = EXCLUDED.updated_at",
            (datetime.now().isoformat(),)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    from database.postgres import PostgresDatabase
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT agent_name, updated_at FROM agent_sessions WHERE status = 'ACTIVE' OR status = 'PAUSED'")
    rows = cursor.fetchall()
    now = datetime.now()
    timeout = False
    for agent, updated_str in rows:
        try:
            updated_time = datetime.fromisoformat(updated_str)
            if (now - updated_time).total_seconds() > 1800:
                cursor.execute("UPDATE agent_sessions SET status = 'EXPIRED', updated_at = %s WHERE agent_name = %s", (now.isoformat(), agent))
                timeout = True
        except Exception:
            pass
    if timeout:
        conn.commit()
        cursor.execute("DELETE FROM agent_session_state")
        conn.commit()
    cursor.close()
    conn.close()
    return False

def detect_intent(question: str) -> Optional[str]:
    question_lower = question.lower()
    if question_lower in {"cancel", "restart", "new trip"}:
        return "general"
        
    # Check multi-word phrases first
    if any(p in question_lower for p in ["things to do", "places to see", "places to visit", "sightseeing"]):
        return "attraction"
    if any(p in question_lower for p in ["plan my day", "day plan", "day-by-day", "time slot"]):
        return "calendar"
    if any(p in question_lower for p in ["trip cost", "reduce cost"]):
        return "budget"
        
    # Use word tokenization to avoid substring matching issues (e.g. "hot" in "hotels", "rain" in "train")
    import re
    words = set(re.findall(r'\b\w+\b', question_lower))
    
    if any(kw in words for kw in ["weather", "rain", "temperature", "forecast", "climate", "sunny", "wind", "humidity", "hot", "cold"]):
        return "weather"
    if any(kw in words for kw in ["train", "railway", "rail", "irctc", "station", "platform"]):
        return "train"
    if any(kw in words for kw in ["hotel", "hotels", "stay", "room", "rooms", "resort", "resorts", "accommodation"]):
        return "hotel"
    if any(kw in words for kw in ["restaurant", "restaurants", "food", "eat", "idli", "dosa", "breakfast", "lunch", "dinner"]):
        return "restaurant"
    if any(kw in words for kw in ["nearby", "place", "places", "tourist", "visit", "attraction", "attractions", "temple", "temples"]):
        return "attraction"
    if any(kw in words for kw in ["trip", "plan", "itinerary", "vacation", "holiday", "tour", "calendar", "schedule", "timetable", "agenda"]):
        return "calendar"
    if any(kw in words for kw in ["budget", "cost", "expense", "estimate", "under", "cheap"]):
        return "budget"
        
    return None

def extract_query_details(question: str) -> dict:
    normalized_question = question.replace('_', ' ')
    question_lower = normalized_question.lower()
    
    if any(kw in question_lower for kw in ["train", "railway", "rail", "irctc"]):
        date_pattern = r'(?:on|in|)\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}[-/]\d{1,2}|\d{4}-\d{1,2}-\d{1,2}|tomorrow|today|next\s+\w+)'
        date_match = re.search(date_pattern, question_lower)
        travel_date = date_match.group(1).strip() if date_match else "None"
        
        query_clean = re.sub(r'train|railway|rail|irctc', '', question_lower).strip()
        
        if ' to ' in query_clean:
            parts = query_clean.split(' to ', 1)
            source_part = parts[0].strip()
            dest_part = parts[1].strip()
            
            if source_part.startswith('from '):
                source = source_part.replace('from', '').strip()
            else:
                source = source_part
            
            destination = re.sub(date_pattern, '', dest_part).strip()
            source = re.sub(r'\b(from|the|a|an)\b', '', source).strip()
            destination = re.sub(r'\b(the|a|an)\b', '', destination).strip()
            source = re.sub(r'\s+', ' ', source).strip()
            destination = re.sub(r'\s+', ' ', destination).strip()
            
            if not destination or len(destination) < 2 or destination.isdigit():
                alt_pattern = r'to\s+([a-z]{2,}(?:\s+[a-z]{2,})?)\s+(?:on|in)?\s*' + date_pattern
                alt_match = re.search(alt_pattern, question_lower)
                if alt_match:
                    destination = alt_match.group(1).strip()
                else:
                    to_index = query_clean.find(' to ')
                    if to_index != -1:
                        after_to = query_clean[to_index + 4:].strip()
                        parts_by_date = re.split(date_pattern, after_to)
                        if parts_by_date and parts_by_date[0].strip():
                            destination = parts_by_date[0].strip()
            
            def is_valid_location(name):
                if not name or len(name) < 2 or name.isdigit():
                    return False
                return True
            
            if is_valid_location(source) and is_valid_location(destination):
                source_clean = re.sub(r'\s+', '', source).upper() if len(source) <= 4 else source.title()
                dest_clean = re.sub(r'\s+', '', destination).upper() if len(destination) <= 4 else destination.title()
                
                return {
                    "city": source_clean,
                    "destination": dest_clean,
                    "travel_date": travel_date,
                    "days": 3,
                    "requires_city": True
                }
    
    prompt = (
        "Analyze the following user query and extract: \n"
        "1. The primary city or source location.\n"
        "2. The destination city.\n"
        "3. The travel date.\n"
        "4. The duration (default 3).\n"
        "5. A boolean 'requires_city'.\n\n"
        "Return strictly JSON: { \"city\": \"...\", \"destination\": \"...\", \"travel_date\": \"...\", \"days\": 3, \"requires_city\": true }\n\n"
        f"Query: {question}"
    )
    try:
        response = client.chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role": "user", "content": prompt}], temperature=0.0)
        data = json.loads(response.choices[0].message.content.strip())
        return {
            "city": data.get("city", "None"),
            "destination": data.get("destination", "None"),
            "travel_date": data.get("travel_date", "None"),
            "days": int(data.get("days", 3)),
            "requires_city": bool(data.get("requires_city", True))
        }
    except Exception:
        return {"city": "None", "destination": "None", "travel_date": "None", "days": 3, "requires_city": True}

def extract_all_opening_details(question: str) -> dict:
    from services.questionnaire_service import extract_calendar_fields
    local_extracted = extract_calendar_fields(question)

    extracted = {
        "destination": local_extracted.get("destination", "None"),
        "current_location": local_extracted.get("current_location", "None"),
        "travel_date": local_extracted.get("travel_date", "None"),
        "days": local_extracted.get("days", "None"),
        "budget": local_extracted.get("budget", "None"),
        "travelers": local_extracted.get("travelers", "None"),
        "travel_style": local_extracted.get("travel_style", "None"),
        "travel_mode": local_extracted.get("travel_mode", "None"),
        "interests": local_extracted.get("interests", "None")
    }

    # If destination was already extracted via deterministic regex/rules, skip slow LLM call
    if extracted["destination"] != "None":
        return extracted

    if client:
        try:
            prompt = (
                "Analyze the following user query and extract travel details: "
                "{ \"destination\": \"...\", \"current_location\": \"...\", \"travel_date\": \"...\", \"days\": \"...\", \"budget\": \"...\", \"travelers\": \"...\", \"travel_style\": \"...\", \"travel_mode\": \"...\", \"interests\": \"...\" }\n\n"
                f"Query: {question}"
            )
            response = client.chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role": "user", "content": prompt}], temperature=0.0)
            content = response.choices[0].message.content.strip()
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                for k, v in data.items():
                    if k in extracted and v and str(v).lower() != "none" and extracted[k] == "None":
                        extracted[k] = str(v)
        except Exception:
            pass

    return extracted

def extract_single_field(field_key: str, user_response: str) -> str:
    prompt = f"The user was asked {field_key}. Response: '{user_response}'. Extract the value. Return only the value."
    try:
        response = client.chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role": "user", "content": prompt}], temperature=0.0)
        return response.choices[0].message.content.strip()
    except Exception:
        return "None"

def matches_keywords(question, keywords):
    question_lower = question.lower()
    for kw in keywords:
        if re.search(r'\b' + re.escape(kw.lower()) + r's?\b', question_lower):
            return True
    return False

def start_agent_questionnaire(agent_name: str, question: str):
    agent_name = normalize_agent(agent_name)
    clear_guided_state()
    update_guided_state("active_agent", agent_name)
    update_guided_state("agent_flow_active", "1")
    update_guided_state("is_active", "0")
    for key, value in extract_agent_initial_values(agent_name, question).items():
        update_guided_state(agent_state_key(agent_name, key), value)

def complete_agent_questionnaire(agent_name: str):
    agent_name = normalize_agent(agent_name)
    update_guided_state("agent_flow_active", "0")
    update_guided_state("last_completed_agent", agent_name)

def route_question(state, details=None):
    question = state["question"].strip()
    question_lower = question.lower()
    demo_log(
        "SUPERVISOR_ROUTE_START",
        f"question={question!r}, city={state.get('city', 'None')}, destination={state.get('destination', 'None')}, mode={state.get('travel_mode', 'None')}"
    )

    def is_exact_choice(text, keywords, num):
        cleaned = text.strip().strip('.')
        if any(kw in text for kw in keywords): return True
        return cleaned == str(num) or cleaned in [f"option {num}", f"choice {num}", f"({num})"]

    if check_session_timeout_and_commands(question):
        return ["general"]

    g_state = get_guided_state()
    trip_status = g_state.get("trip_status")

    if trip_status == "preview":
        if any(kw in question_lower for kw in ["reset", "start over", "new trip"]): clear_guided_state()
        elif is_exact_choice(question_lower, ["save", "keep"], 1): return ["save_itinerary"]
        elif is_exact_choice(question_lower, ["regenerate", "redo", "recreate"], 3): return ["regenerate_itinerary"]
        elif any(kw in question_lower for kw in ["delete", "remove", "cancel", "discard"]): return ["delete_itinerary"]
        else:
            is_modification = any(verb in question_lower for verb in ["replace", "change", "add", "remove", "delete", "swap", "modify", "update"])
            is_info_query = any(kw in question_lower for kw in ["list", "show", "find", "suggest", "recommend", "weather", "restaurant", "hotel", "attraction", "place"])
            if not is_modification and is_info_query: pass
            else: return ["modify_itinerary"]

    elif trip_status == "calendar_sync":
        if any(kw in question_lower for kw in ["reset", "start over", "new trip"]): clear_guided_state()
        elif is_exact_choice(question_lower, ["yes", "sync", "google calendar", "calendar"], 2) or question_lower.strip().strip('.') in ["yes", "y"]: return ["google_calendar"]
        else: clear_guided_state()

    detected_intent = detect_intent(question)
    init_guided_db()
    from database.postgres import PostgresDatabase
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT agent_name FROM agent_sessions WHERE status = 'ACTIVE'")
    active_row = cursor.fetchone()
    cursor.execute("SELECT agent_name FROM agent_sessions WHERE status = 'PAUSED'")
    paused_row = cursor.fetchone()
    cursor.close()
    conn.close()

    if active_row:
        active_agent = active_row[0]
        g_state = get_guided_state()
        missing_key, missing_prompt = get_next_missing_agent_field(active_agent, g_state)
        demo_log("SUPERVISOR_ACTIVE_SESSION", f"agent={active_agent}, missing={missing_key or 'none'}")

        # During the calendar questionnaire, short answers like "Train",
        # "Bus", "Car", "Flight", "moderate", or "2" are field answers, not
        # new intents. Handle the pending field before allowing intent
        # interruption, otherwise the flow stops early and the app falls back
        # to a generic trip response.
        can_interrupt_questionnaire = True
        if active_agent == "calendar" and missing_key in {
            "travel_mode",
            "budget",
            "travelers",
            "travel_style",
            "interests",
            "days",
            "current_location",
            "travel_date",
        }:
            can_interrupt_questionnaire = False

        if can_interrupt_questionnaire and detected_intent and detected_intent != active_agent and detected_intent in {"weather", "train"}:
            update_agent_session(active_agent, status="PAUSED")
            update_guided_state("active_agent", "")
            demo_log("SUPERVISOR_ROUTE_DECISION", f"paused_agent={active_agent}, interrupt_intent={detected_intent}, routes={[detected_intent]}")
            return [detected_intent]

        if missing_key:
            save_agent_answer(active_agent, missing_key, question)
            g_state = get_guided_state()
            next_key, next_prompt = get_next_missing_agent_field(active_agent, g_state)
            meta = get_progress_metadata(active_agent, g_state)
            next_key, next_prompt = get_next_missing_agent_field(active_agent, g_state)
            meta = get_progress_metadata(active_agent, g_state)
            update_agent_session(active_agent, status="ACTIVE", last_question=missing_prompt, next_question=next_prompt or "", completed_count=meta["completed"])
            if next_key:
                demo_log("SUPERVISOR_ROUTE_DECISION", f"agent={active_agent}, saved_field={missing_key}, next_field={next_key}, routes=['merge']")
                return ["merge"]
            complete_agent_questionnaire(active_agent)
            completed_routes = [route_for_agent(active_agent)]
            demo_log("SUPERVISOR_ROUTE_DECISION", f"agent={active_agent}, completed=yes, routes={completed_routes}")
            return completed_routes

    elif paused_row:
        paused_agent = paused_row[0]
        if detected_intent in {"weather", "train"}:
            demo_log("SUPERVISOR_ROUTE_DECISION", f"paused_agent={paused_agent}, interrupt_intent={detected_intent}, routes={[detected_intent]}")
            return [detected_intent]
        update_agent_session(paused_agent, status="ACTIVE")
        update_guided_state("active_agent", paused_agent)
        g_state = get_guided_state()
        missing_key, missing_prompt = get_next_missing_agent_field(paused_agent, g_state)
        if missing_key:
            save_agent_answer(paused_agent, missing_key, question)
            g_state = get_guided_state()
            next_key, next_prompt = get_next_missing_agent_field(paused_agent, g_state)
            meta = get_progress_metadata(paused_agent, g_state)
            update_agent_session(paused_agent, status="ACTIVE", last_question=missing_prompt, next_question=next_prompt or "", completed_count=meta["completed"])
            if next_key:
                demo_log("SUPERVISOR_ROUTE_DECISION", f"resumed_agent={paused_agent}, saved_field={missing_key}, next_field={next_key}, routes=['merge']")
                return ["merge"]
            complete_agent_questionnaire(paused_agent)
            completed_routes = [route_for_agent(paused_agent)]
            demo_log("SUPERVISOR_ROUTE_DECISION", f"resumed_agent={paused_agent}, completed=yes, routes={completed_routes}")
            return completed_routes

    is_start = (any(k in question_lower for k in ["trip", "plan", "itinerary", "vacation", "holiday", "tour", "reset", "start over"]) or (details and details.get("city") != "None")) and detected_intent not in ["hotel", "restaurant", "weather", "attraction"]
    if is_start:
        agent_name = "calendar"
        g_state = get_guided_state()
        missing_field, missing_prompt = get_next_missing_agent_field(agent_name, g_state)
        if missing_field:
            start_agent_questionnaire(agent_name, question)
            g_state = get_guided_state()
            meta = get_progress_metadata(agent_name, g_state)
            update_agent_session(agent_name, status="ACTIVE", next_question=get_next_missing_agent_field(agent_name, g_state)[1] or "", completed_count=meta["completed"])
            demo_log("SUPERVISOR_ROUTE_DECISION", f"start_trip=yes, missing_field={missing_field}, routes=['merge']")
            return ["merge"]
        else:
            routes = ["hotel", "restaurant", "nearby", "weather", "transport", "calendar"]
            demo_log("SUPERVISOR_ROUTE_DECISION", f"start_trip=yes, all_fields_present=yes, routes={routes}")
            return routes

    routes = []
    mk = lambda q, kw: matches_keywords(q, kw)
    if mk(question_lower, ["train", "railway", "rail"]): routes.append("transport")
    if mk(question_lower, ["restaurant", "food", "eat"]): routes.append("restaurant")
    if mk(question_lower, ["hotel", "stay"]): routes.append("hotel")
    if mk(question_lower, ["nearby", "place", "attraction"]) and not routes: routes.append("nearby")
    if mk(question_lower, ["weather", "rain"]): routes.append("weather")
    if mk(question_lower, ["calendar", "schedule"]): routes.append("calendar")
    
    routes = list(set(routes))
    if not routes: routes.append("general")
    if len(routes) == 1 and routes[0] in {"hotel", "restaurant", "nearby", "calendar", "budget"}:
        if routes[0] != "calendar" and (clean_val(state.get("destination")) or clean_val(state.get("city"))):
            demo_log("SUPERVISOR_ROUTE_DECISION", f"single_agent={routes[0]}, city_present=yes, routes={routes}")
            return routes
        agent_name = "attraction" if routes[0] == "nearby" else routes[0]
        start_agent_questionnaire(agent_name, question)
        g_state = get_guided_state()
        meta = get_progress_metadata(agent_name, g_state)
        update_agent_session(agent_name, status="ACTIVE", next_question=get_next_missing_agent_field(agent_name, g_state)[1] or "", completed_count=meta["completed"])
        final_routes = ["merge"] if get_next_missing_agent_field(agent_name, g_state)[0] else [route_for_agent(agent_name)]
        demo_log("SUPERVISOR_ROUTE_DECISION", f"single_agent={agent_name}, routes={final_routes}")
        return final_routes

    demo_log("SUPERVISOR_ROUTE_DECISION", f"detected_intent={detected_intent or 'none'}, routes={routes}")
    return routes
