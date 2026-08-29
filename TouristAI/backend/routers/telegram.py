import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request

from backend.AI.app import ChatRequest, chat
from backend.AI.agents.concierge_agent import concierge_agent
from backend.AI.database.postgres import PostgresDatabase
from backend.AI.repositories.trip_repository import TripRepository
from backend.AI.session_context import set_session_id
from backend.AI.supervisor import get_guided_state
from backend.AI.services.telegram_service import (
    TelegramConfigurationError,
    api_call,
    is_user_allowed,
    questionnaire_keyboard,
    register_webhook,
    send_message,
    verify_webhook_secret,
    webhook_info,
    webhook_secret,
)


router = APIRouter()


def _claim_update(update_id: int) -> bool:
    PostgresDatabase.initialize()
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM telegram_updates WHERE update_id=%s", (update_id,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return False
    cursor.execute("INSERT INTO telegram_updates (update_id,processed_at,status) VALUES (%s,%s,%s)", (update_id, datetime.now(timezone.utc).isoformat(), "received"))
    conn.commit()
    cursor.close()
    conn.close()
    return True


def _mark_update(update_id: int, status: str) -> None:
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE telegram_updates SET processed_at=%s,status=%s WHERE update_id=%s", (datetime.now(timezone.utc).isoformat(), status, update_id))
    conn.commit()
    cursor.close()
    conn.close()


def _save_account(user: Dict[str, Any], chat_id: Any) -> None:
    now = datetime.now(timezone.utc).isoformat()
    display_name = " ".join(filter(None, [user.get("first_name"), user.get("last_name")])).strip()
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO telegram_accounts (telegram_user_id,telegram_chat_id,username,display_name,last_seen_at) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (telegram_user_id) DO UPDATE SET telegram_chat_id=EXCLUDED.telegram_chat_id,username=EXCLUDED.username,display_name=EXCLUDED.display_name,last_seen_at=EXCLUDED.last_seen_at",
        (str(user.get("id")), str(chat_id), user.get("username"), display_name, now),
    )
    conn.commit()
    cursor.close()
    conn.close()


def _help_text() -> str:
    return (
        "TouristAI commands:\n"
        "/plan - create a trip\n/mytrip - view the active trip\n/next - next activity\n"
        "/budget - trip budget\n/weather - trip weather\n/transport - search transport\n"
        "/hotels - find hotels\n/food - find restaurants\n/nearby - discover attractions\n"
        "/concierge <request> - ask the active-trip AI Concierge\n"
        "/whoami - show your Telegram user ID\n/help - commands\n\n"
        "You can also type a normal request, for example: Plan a 3-day Delhi trip for 2 people under ₹30,000."
    )


def _command_to_question(text: str) -> Optional[str]:
    command, _, args = text.strip().partition(" ")
    command = command.split("@", 1)[0].lower()
    mapping = {
        "/plan": f"Plan a trip {args}".strip(),
        "/next": "What's next on my itinerary?",
        "/budget": "How much budget is remaining?",
        "/weather": f"Weather {args}".strip(),
        "/transport": f"Find transport {args}".strip(),
        "/hotels": f"Find hotels {args}".strip(),
        "/food": f"Find restaurants {args}".strip(),
        "/nearby": f"Find nearby attractions {args}".strip(),
        "/mytrip": "Show my current trip",
    }
    return mapping.get(command)


def _active_trip_for_concierge(session_id: str) -> Dict[str, Any]:
    set_session_id(session_id)
    state = get_guided_state()
    raw_items = []
    if state.get("last_itinerary_items"):
        try:
            raw_items = json.loads(state["last_itinerary_items"])
        except (TypeError, ValueError):
            raw_items = []
    trip_id = state.get("trip_id")
    repo = TripRepository()
    trip_record = repo.get_trip(trip_id) if trip_id else None
    if not raw_items and trip_id:
        raw_items = [item.model_dump() if hasattr(item, "model_dump") else item.dict() for item in repo.get_itinerary_items(trip_id)]
    details = repo.get_trip_details(trip_id) if trip_id else None
    itinerary: Dict[int, list] = {}
    for item in raw_items:
        day = int(item.get("day") or 1)
        itinerary.setdefault(day, []).append({
            **item,
            "id": item.get("activity_id") or item.get("id"),
            "title": item.get("title") or item.get("activity"),
            "time": item.get("time") or item.get("start_time"),
            "description": item.get("description") or item.get("notes"),
        })
    return {
        "id": trip_id,
        "cityName": (trip_record.city if trip_record else None) or state.get("destination") or state.get("city") or "your destination",
        "startDate": (trip_record.travel_date if trip_record else None) or state.get("travel_date"),
        "currentLocation": (trip_record.current_location if trip_record else None) or state.get("current_location"),
        "itinerary": itinerary,
        "budgetSummary": (details or {}).get("budget_summary", {}),
        "weatherSummary": (details or {}).get("weather_summary", ""),
        "hotels": (details or {}).get("hotels", []),
        "restaurants": (details or {}).get("restaurants", []),
        "emergencyContacts": (details or {}).get("emergency", []),
    }


def _process_concierge(chat_id: Any, user_id: Any, text: str) -> None:
    _, _, request_text = text.strip().partition(" ")
    if not request_text.strip():
        send_message(
            chat_id,
            "AI Concierge is ready for your active trip.\n\n"
            "Try:\n"
            "/concierge what's next\n"
            "/concierge book a local cab to my next stop\n"
            "/concierge check my budget\n"
            "/concierge find vegetarian food",
        )
        return
    session_id = f"telegram:{chat_id}"
    trip = _active_trip_for_concierge(session_id)
    result = concierge_agent(request_text, trip, trip.get("currentLocation"))
    reply_markup = None
    action = result.get("action") or {}
    if action.get("type") == "open_url" and str(action.get("url") or "").startswith("https://"):
        reply_markup = {"inline_keyboard": [[{"text": action.get("label") or "Open", "url": action["url"]}]]}
    send_message(chat_id, result.get("answer") or "I could not complete that Concierge request.", reply_markup)


def _process_update(update_id: int, user: Dict[str, Any], chat_id: Any, text: str, callback_query_id: Optional[str] = None) -> None:
    try:
        if callback_query_id:
            api_call("answerCallbackQuery", {"callback_query_id": callback_query_id})
        if not is_user_allowed(user.get("id")):
            send_message(chat_id, "This TouristAI bot is currently restricted to approved demo users.")
            _mark_update(update_id, "denied")
            return
        _save_account(user, chat_id)
        normalized = text.strip()
        command = normalized.split(" ", 1)[0].split("@", 1)[0].lower()
        if command in {"/start", "/help"}:
            send_message(chat_id, "Welcome to TouristAI!\n\n" + _help_text())
            _mark_update(update_id, "completed")
            return
        if command == "/whoami":
            send_message(chat_id, f"Your Telegram user ID is: {user.get('id')}")
            _mark_update(update_id, "completed")
            return
        if command == "/concierge":
            _process_concierge(chat_id, user.get("id"), normalized)
            _mark_update(update_id, "completed")
            return
        question = _command_to_question(normalized) or normalized
        send_message(chat_id, "TouristAI is working on your request…")
        result = chat(ChatRequest(
            question=question,
            user_id=f"telegram:{user.get('id')}",
            session_id=f"telegram:{chat_id}",
        ))
        answer = result.get("answer") or "I could not generate a response."
        send_message(chat_id, answer, questionnaire_keyboard(answer))
        _mark_update(update_id, "completed")
    except Exception as exc:
        print(f"[LOG][TELEGRAM_ERROR] update_id={update_id}, type={type(exc).__name__}")
        try:
            send_message(chat_id, "TouristAI could not complete that request. Please try again.")
        except Exception:
            pass
        _mark_update(update_id, "failed")


@router.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks, x_telegram_bot_api_secret_token: Optional[str] = Header(default=None)):
    if not verify_webhook_secret(x_telegram_bot_api_secret_token):
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")
    update = await request.json()
    update_id = int(update.get("update_id", 0))
    if not update_id or not _claim_update(update_id):
        return {"ok": True}
    callback = update.get("callback_query") or {}
    message = update.get("message") or callback.get("message") or {}
    user = callback.get("from") or message.get("from") or {}
    chat_id = (message.get("chat") or {}).get("id")
    text = message.get("text") or ""
    if callback.get("data", "").startswith("answer:"):
        text = callback["data"].split(":", 1)[1]
    if chat_id and user.get("id") and text:
        background_tasks.add_task(_process_update, update_id, user, chat_id, text, callback.get("id"))
    else:
        _mark_update(update_id, "ignored")
    return {"ok": True}


def _verify_admin_secret(value: Optional[str]) -> None:
    try:
        valid = value and value == webhook_secret()
    except TelegramConfigurationError:
        valid = False
    if not valid:
        raise HTTPException(status_code=403, detail="Invalid admin secret")


@router.post("/register-webhook")
def telegram_register_webhook(x_telegram_admin_secret: Optional[str] = Header(default=None)):
    _verify_admin_secret(x_telegram_admin_secret)
    public_url = os.getenv("PUBLIC_BACKEND_URL", "").strip()
    if not public_url.startswith("https://"):
        raise HTTPException(status_code=400, detail="PUBLIC_BACKEND_URL must be a public HTTPS URL")
    return register_webhook(public_url)


@router.get("/status")
def telegram_status(x_telegram_admin_secret: Optional[str] = Header(default=None)):
    _verify_admin_secret(x_telegram_admin_secret)
    return {"configured": True, "webhook": webhook_info()}
