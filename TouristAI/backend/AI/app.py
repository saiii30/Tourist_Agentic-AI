import os
import sqlite3
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Response
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from graph import graph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

def init_calendar_db():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tourist_ai.db"))
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_name TEXT,
                day_num INTEGER,
                time_slot TEXT,
                time_range TEXT,
                activity TEXT,
                details TEXT
            )
        """)
        conn.commit()
        conn.close()
        print("Calendar events table initialized successfully.")
    except Exception as e:
        print(f"Error initializing calendar events table: {e}")

@app.on_event("startup")
def startup_event():
    init_calendar_db()

class ChatRequest(BaseModel):
    question: str

class SaveCalendarRequest(BaseModel):
    itinerary_text: str
    trip_name: str = None

@app.post("/chat")
def chat(req: ChatRequest):
    result = graph.invoke(
        {
            "question": req.question,
            "responses": []
        }
    )
    return {
        "answer": result["answer"],
        "routes": result.get("routes", [])
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
            (trip_name,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return Response(f"No events found for trip '{trip_name}'", status_code=404)
            
        # Generate ICS content
        ics = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//TouristAI//ItineraryExporter//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH"
        ]
        
        # We assign a default starting date for the calendar events (tomorrow)
        base_date = datetime.now() + timedelta(days=1)
        
        for row in rows:
            day_num, time_slot, time_range, activity, details = row
            
            # Map day_num to a specific date relative to base_date
            event_date = base_date + timedelta(days=(day_num - 1))
            date_str = event_date.strftime("%Y%m%d")
            
            # Map time slot to specific hours
            start_hour, end_hour = 9, 12
            if time_slot.lower() == "afternoon":
                start_hour, end_hour = 13, 17
            elif time_slot.lower() == "evening":
                start_hour, end_hour = 18, 21
                
            start_time = f"{date_str}T{start_hour:02d}0000"
            end_time = f"{date_str}T{end_hour:02d}0000"
            
            # Escape characters for standard ICS format
            summary_esc = activity.replace(",", "\\,").replace(";", "\\;")
            desc_esc = details.replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
            
            ics.extend([
                "BEGIN:VEVENT",
                f"SUMMARY:{summary_esc}",
                f"DESCRIPTION:{desc_esc}",
                f"DTSTART;TZID=Asia/Kolkata:{start_time}",
                f"DTEND;TZID=Asia/Kolkata:{end_time}",
                f"UID:{trip_name.replace(' ', '_')}_day{day_num}_{time_slot}_{datetime.now().microsecond}@touristai.com",
                f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
                "END:VEVENT"
            ])
            
        ics.append("END:VCALENDAR")
        ics_content = "\r\n".join(ics)
        
        filename = f"{trip_name.replace(' ', '_')}_itinerary.ics"
        return Response(
            content=ics_content,
            media_type="text/calendar",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        print(f"Error exporting calendar: {e}")
        return Response(f"Error exporting calendar: {str(e)}", status_code=500)