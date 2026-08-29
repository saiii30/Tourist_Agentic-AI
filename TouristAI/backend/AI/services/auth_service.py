import base64
import hashlib
import hmac
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from backend.AI.database.postgres import PostgresDatabase


PASSWORD_ITERATIONS = 310_000
SESSION_HOURS = 24 * 7


def normalize_email(email: str) -> str:
    value = str(email or "").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
        raise ValueError("Enter a valid email address.")
    return value


def validate_password(password: str) -> None:
    value = str(password or "")
    if len(value) < 10 or not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise ValueError("Password must be at least 10 characters and contain a letter and a number.")


def hash_password(password: str, salt: Optional[bytes] = None, iterations: int = PASSWORD_ITERATIONS) -> Tuple[str, str, int]:
    validate_password(password)
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return base64.b64encode(digest).decode("ascii"), base64.b64encode(salt).decode("ascii"), iterations


def verify_password(password: str, encoded_hash: str, encoded_salt: str, iterations: int) -> bool:
    try:
        salt = base64.b64decode(encoded_salt.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        expected = base64.b64decode(encoded_hash.encode("ascii"))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_user(email: str, password: str, display_name: str) -> dict:
    email = normalize_email(email)
    display_name = str(display_name or "").strip()
    if len(display_name) < 2:
        raise ValueError("Display name must contain at least 2 characters.")
    password_hash, salt, iterations = hash_password(password)
    now = datetime.now(timezone.utc).isoformat()
    user_id = f"user:{uuid.uuid4()}"
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO auth_users (user_id, email, display_name, password_hash, password_salt, password_iterations, created_at, updated_at, disabled) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,0)",
            (user_id, email, display_name, password_hash, salt, iterations, now, now),
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
            raise ValueError("An account with this email already exists.") from exc
        raise
    finally:
        cursor.close()
        conn.close()
    return {"user_id": user_id, "email": email, "display_name": display_name}


def authenticate(email: str, password: str) -> Optional[dict]:
    email = normalize_email(email)
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, email, display_name, password_hash, password_salt, password_iterations, disabled FROM auth_users WHERE email = %s", (email,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row or row[6] or not verify_password(password, row[3], row[4], row[5]):
        return None
    return {"user_id": row[0], "email": row[1], "display_name": row[2]}


def create_access_token(user_id: str) -> Tuple[str, str]:
    token = secrets.token_urlsafe(48)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=SESSION_HOURS)
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO auth_sessions (token_hash, user_id, created_at, expires_at) VALUES (%s,%s,%s,%s)", (_token_hash(token), user_id, now.isoformat(), expires.isoformat()))
    conn.commit()
    cursor.close()
    conn.close()
    return token, expires.isoformat()


def get_user_for_token(token: str) -> Optional[dict]:
    now = datetime.now(timezone.utc).isoformat()
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT u.user_id, u.email, u.display_name FROM auth_sessions s JOIN auth_users u ON u.user_id=s.user_id WHERE s.token_hash=%s AND s.revoked_at IS NULL AND s.expires_at>%s AND u.disabled=0",
        (_token_hash(token), now),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return {"user_id": row[0], "email": row[1], "display_name": row[2]} if row else None


def revoke_token(token: str) -> None:
    conn = PostgresDatabase.get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE auth_sessions SET revoked_at=%s WHERE token_hash=%s", (datetime.now(timezone.utc).isoformat(), _token_hash(token)))
    conn.commit()
    cursor.close()
    conn.close()
