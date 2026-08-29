import hmac
import os
import re
from typing import Any, Dict, Iterable, List, Optional

import requests


class TelegramConfigurationError(RuntimeError):
    pass


def bot_token() -> str:
    value = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not value:
        raise TelegramConfigurationError("TELEGRAM_BOT_TOKEN is not configured")
    return value


def webhook_secret() -> str:
    value = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if not value:
        raise TelegramConfigurationError("TELEGRAM_WEBHOOK_SECRET is not configured")
    return value


def verify_webhook_secret(received: Optional[str]) -> bool:
    try:
        expected = webhook_secret()
    except TelegramConfigurationError:
        return False
    return bool(received) and hmac.compare_digest(str(received), expected)


def allowed_user_ids() -> set[str]:
    return {item.strip() for item in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",") if item.strip()}


def demo_mode() -> bool:
    return os.getenv("TELEGRAM_DEMO_MODE", "true").strip().lower() in {"1", "true", "yes", "on"}


def is_user_allowed(user_id: Any) -> bool:
    allowed = allowed_user_ids()
    return not demo_mode() or (bool(allowed) and str(user_id) in allowed)


def api_call(method: str, payload: Optional[Dict[str, Any]] = None, timeout: float = 15.0) -> Dict[str, Any]:
    response = requests.post(
        f"https://api.telegram.org/bot{bot_token()}/{method}",
        json=payload or {},
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API request failed: {data.get('description', 'unknown error')}")
    return data


def split_message(text: str, limit: int = 3900) -> List[str]:
    cleaned = re.sub(r"\n?\[SOURCE:[^\]]+\]\s*$", "", str(text or "").strip())
    if not cleaned:
        return ["I could not generate a response for that request."]
    chunks = []
    while len(cleaned) > limit:
        split_at = cleaned.rfind("\n", 0, limit)
        if split_at < limit // 2:
            split_at = cleaned.rfind(" ", 0, limit)
        if split_at <= 0:
            split_at = limit
        chunks.append(cleaned[:split_at].strip())
        cleaned = cleaned[split_at:].strip()
    if cleaned:
        chunks.append(cleaned)
    return chunks


def send_message(chat_id: Any, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> None:
    chunks = split_message(text)
    for index, chunk in enumerate(chunks):
        payload: Dict[str, Any] = {"chat_id": chat_id, "text": chunk, "disable_web_page_preview": True}
        if index == len(chunks) - 1 and reply_markup:
            payload["reply_markup"] = reply_markup
        api_call("sendMessage", payload)


def questionnaire_keyboard(answer: str) -> Optional[Dict[str, Any]]:
    lower = str(answer or "").lower()
    options: List[str] = []
    if "mode of travel" in lower:
        options = ["Car", "Bus", "Train", "Flight"]
    elif "budget" in lower and any(item in lower for item in ["low", "moderate", "luxury"]):
        options = ["Low", "Moderate", "Luxury"]
    elif any(term in lower for term in ["do you want", "should i", "do you need", "sync after"]):
        options = ["Yes", "No"]
    if not options:
        return None
    rows = [[{"text": option, "callback_data": f"answer:{option}"} for option in options[i:i + 2]] for i in range(0, len(options), 2)]
    return {"inline_keyboard": rows}


def register_webhook(public_backend_url: str) -> Dict[str, Any]:
    url = public_backend_url.rstrip("/") + "/api/telegram/webhook"
    return api_call("setWebhook", {
        "url": url,
        "secret_token": webhook_secret(),
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": True,
    })


def webhook_info() -> Dict[str, Any]:
    return api_call("getWebhookInfo").get("result", {})
