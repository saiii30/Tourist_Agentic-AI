import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import get_connection, init_chat_db
from graph import graph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def init_calendar_db():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tourist_ai.db"))
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_name TEXT,
                day_num INTEGER,
                time_slot TEXT,
                time_range TEXT,
                activity TEXT,
                details TEXT
            )
            """
        )
        conn.commit()
        conn.close()
        print("Calendar events table initialized successfully.")
    except Exception as e:
        print(f"Error initializing calendar events table: {e}")


@app.on_event("startup")
def startup_event():
    init_calendar_db()
    init_chat_db()


class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[int] = None


class CreateConversationRequest(BaseModel):
    title: str


class RenameConversationRequest(BaseModel):
    title: str


class SaveCalendarRequest(BaseModel):
    itinerary_text: str
    trip_name: str = None


def _normalize_title(text: str) -> str:
    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return "New chat"
    return cleaned[:40] if len(cleaned) > 40 else cleaned


@app.get("/conversations")
def list_conversations():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, title, created_at FROM conversations ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [
        {"id": row["id"], "title": row["title"], "created_at": row["created_at"]}
        for row in rows
    ]


@app.post("/conversation")
def create_conversation(req: CreateConversationRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversations (title) VALUES (?)", (_normalize_title(req.title),))
    conn.commit()
    conversation_id = cursor.lastrowid
    conn.close()
    return {"id": conversation_id, "title": _normalize_title(req.title)}


@app.get("/conversation/{conversation_id}")
def get_conversation(conversation_id: int):
    conn = get_connection()
    conversation = conn.execute(
        "SELECT id, title FROM conversations WHERE id = ?",
        (conversation_id,),
    ).fetchone()
    if not conversation:
        conn.close()
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = conn.execute(
        "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id",
        (conversation_id,),
    ).fetchall()
    conn.close()
    return {
        "id": conversation["id"],
        "title": conversation["title"],
        "messages": [
            {"role": message["role"], "text": message["content"]}
            for message in messages
        ],
    }


@app.delete("/conversation/{conversation_id}")
def delete_conversation(conversation_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()
    return {"success": True}


@app.put("/conversation/{conversation_id}/title")
def rename_conversation(conversation_id: int, req: RenameConversationRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE conversations SET title = ? WHERE id = ?", (_normalize_title(req.title), conversation_id))
    conn.commit()
    conn.close()
    return {"success": True}


@app.post("/chat")
def chat(req: ChatRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    conversation_id = req.conversation_id
    if conversation_id is None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversations (title) VALUES (?)", (_normalize_title(req.question),))
        conn.commit()
        conversation_id = cursor.lastrowid
        conn.close()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
        (conversation_id, "user", req.question.strip()),
    )
    conn.commit()
    conn.close()

    result = graph.invoke({"question": req.question, "responses": []})
    answer = result.get("answer", "")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
        (conversation_id, "assistant", answer),
    )
    conn.commit()
    conn.close()

    return {
        "answer": answer,
        "routes": result.get("routes", []),
        "conversation_id": conversation_id,
    }


@app.post("/calendar/save")
def save_calendar(req: SaveCalendarRequest):
    from supervisor import save_itinerary_to_db

    return save_itinerary_to_db(req.itinerary_text, req.trip_name)


@app.get("/calendar/export")
def export_calendar(trip_name: str):
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tourist_ai.db"))
    if not os.path.exists(db_path):
        return Response("Database not found", status_code=404)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT day_num, time_slot, time_range, activity, details FROM calendar_events WHERE trip_name = ? ORDER BY day_num, id",
            (trip_name,),
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return Response(f"No events found for trip '{trip_name}'", status_code=404)

        ics = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//TouristAI//ItineraryExporter//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]

        base_date = datetime.now() + timedelta(days=1)

        for row in rows:
            day_num, time_slot, time_range, activity, details = row

            event_date = base_date + timedelta(days=(day_num - 1))
            date_str = event_date.strftime("%Y%m%d")

            start_hour, end_hour = 9, 12
            if time_slot.lower() == "afternoon":
                start_hour, end_hour = 13, 17
            elif time_slot.lower() == "evening":
                start_hour, end_hour = 18, 21

            start_time = f"{date_str}T{start_hour:02d}0000"
            end_time = f"{date_str}T{end_hour:02d}0000"

            summary_esc = activity.replace(",", "\\,").replace(";", "\\;")
            desc_esc = details.replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")

            ics.extend(
                [
                    "BEGIN:VEVENT",
                    f"SUMMARY:{summary_esc}",
                    f"DESCRIPTION:{desc_esc}",
                    f"DTSTART;TZID=Asia/Kolkata:{start_time}",
                    f"DTEND;TZID=Asia/Kolkata:{end_time}",
                    f"UID:{trip_name.replace(' ', '_')}_day{day_num}_{time_slot}_{datetime.now().microsecond}@touristai.com",
                    f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
                    "END:VEVENT",
                ]
            )

        ics.append("END:VCALENDAR")
        ics_content = "\r\n".join(ics)

        filename = f"{trip_name.replace(' ', '_')}_itinerary.ics"
        return Response(
            content=ics_content,
            media_type="text/calendar",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        print(f"Error exporting calendar: {e}")
        return Response(f"Error exporting calendar: {str(e)}", status_code=500)