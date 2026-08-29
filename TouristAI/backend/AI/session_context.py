import re
from contextvars import ContextVar


_session_id: ContextVar[str] = ContextVar("tourist_ai_session_id", default="web:guest_user")


def normalize_session_id(value: str | None) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9:_-]", "", str(value or "").strip())[:160]
    return cleaned or "web:guest_user"


def set_session_id(value: str | None) -> str:
    normalized = normalize_session_id(value)
    _session_id.set(normalized)
    return normalized


def get_session_id() -> str:
    return _session_id.get()
