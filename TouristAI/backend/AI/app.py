import os
import sqlite3
import json
import sys
from datetime import datetime, timedelta
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Adjust path to import correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.google_calendar_service import GoogleCalendarService
from services.calendar_service import CalendarService
from services.trip_service import TripService
from services.packing_service import PackingService
from services.budget_service import BudgetService
from services.emergency_service import EmergencyService
from supervisor import get_guided_state, update_guided_state
from graph import graph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

trip_service = TripService()

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
    question_lower = req.question.strip().lower()
    
    # 0. Intercept Travel Booking / Confirmation Texts
    ticket_keywords = ["confirmation number", "pnr", "boarding pass", "e-ticket", "train to", "flight to", "booking reference", "organiser:", "departure:", "arrival:"]
    is_ticket = any(kw in question_lower for kw in ticket_keywords) or ("train" in question_lower and "mdu" in question_lower)
    
    if is_ticket:
        from services.reservation_service import ReservationService
        sync_res = ReservationService.sync_reservation(req.question)
        if sync_res.get("success"):
            details = sync_res["details"]
            mode_text = " (Simulated Mode - Credentials not configured)" if sync_res.get("simulated") else ""
            ans = (
                f"📅 **Travel Booking Synced to Google Calendar!**{mode_text}\n\n"
                f"I have successfully extracted the reservation details and created an event on your primary Google Calendar.\n\n"
                f"- **Event:** {details.get('title')}\n"
                f"- **Departure/Start:** {details.get('start_time')}\n"
                f"- **Arrival/End:** {details.get('end_time')}\n"
                f"- **Location:** {details.get('location')}\n\n"
                f"**Event Description Details:**\n"
                f"```text\n"
                f"{details.get('description')}\n"
                f"```"
            )
            return {
                "status": "success",
                "answer": ans,
                "routes": ["calendar"],
                "trip": None,
                "metadata": {
                    "source": "reservation_service",
                    "generated_by": "llm",
                    "cached": False,
                    "generated_at": datetime.now().isoformat()
                }
            }
        else:
            return {
                "status": "error",
                "answer": f"I detected a travel reservation, but failed to sync it to Google Calendar: {sync_res.get('message')}",
                "routes": ["general"],
                "trip": None,
                "metadata": {
                    "source": "reservation_service",
                    "generated_by": "llm",
                    "cached": False,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
    # 1. Cache Check: Check if this is a start planning query with all criteria
    from supervisor import matches_keywords, extract_all_opening_details, update_guided_state
    
    # Deactivate guided planning if a new single-topic query is asked, to escape any stuck flow
    is_single_topic = any(kw in question_lower for kw in ["weather", "forecast", "climate", "temperature", "rain", "hotel", "stay", "resort", "restaurant", "food", "eat", "cafe", "attraction", "sightseeing", "places to visit", "things to do"])
    if is_single_topic:
        update_guided_state("is_active", "0")
        
    start_keywords = ["trip", "plan", "itinerary", "vacation", "holiday", "tour", "reset", "start over"]
    is_start = matches_keywords(question_lower, start_keywords)
    
    g_state = get_guided_state()
    is_active = g_state.get("is_active") == "1"
    
    if not is_start and not is_active:
        is_single_topic = any(kw in question_lower for kw in ["weather", "forecast", "climate", "temperature", "rain", "hotel", "stay", "resort", "restaurant", "food", "eat", "cafe", "attraction", "sightseeing", "places to visit", "things to do"])
        if not is_single_topic:
            from supervisor import extract_query_details
            details = extract_query_details(req.question)
            if details.get("city") != "None" and details.get("requires_city", True):
                is_start = True
            
    if is_start:
        extracted = extract_all_opening_details(req.question)
        city = extracted.get("destination", "None")
        days_str = extracted.get("days", "None")
        budget = extracted.get("budget", "None")
        travel_style = extracted.get("travel_style", "None")
        
        if city != "None" and days_str != "None" and budget != "None" and travel_style != "None":
            try:
                days = int(days_str)
                cached_trip = trip_service.get_cached_trip(city, days, budget, travel_style)
                if cached_trip:
                    # Update guided state for session continuity
                    update_guided_state("destination", city)
                    update_guided_state("days", str(days))
                    update_guided_state("budget", budget)
                    update_guided_state("travel_style", travel_style)
                    update_guided_state("trip_id", cached_trip["trip"]["trip_id"])
                    update_guided_state("is_active", "0")
                    
                    return {
                        "status": "success",
                        "answer": f"I found a cached trip plan for {city.title()} matching your request in the local database! Here is your saved itinerary.",
                        "routes": ["calendar", "hotel", "restaurant", "nearby", "weather"],
                        "trip": cached_trip["trip"],
                        "metadata": cached_trip["metadata"]
                    }
            except Exception as e:
                print(f"Error checking cache: {e}")

    # 2. Cache Miss: Run LangGraph pipeline
    result = graph.invoke(
        {
            "question": req.question,
            "responses": [],
            "city": "None",
            "days": 3,
            "budget": "None",
            "travelers": 1,
            "travel_style": "None",
            "interests": "None"
        }
    )
    
    g_state = get_guided_state()
    last_items = g_state.get("last_itinerary_items")
    real_itinerary = None
    
    if last_items:
        try:
            items = json.loads(last_items)
            real_itinerary = {}
            for item in items:
                day = item.get("day", 1)
                day_str = str(day)
                if day_str not in real_itinerary:
                    real_itinerary[day_str] = []
                
                start = item.get("start_time", "09:00")
                try:
                    time_str = datetime.strptime(start, "%H:%M").strftime("%I:%M %p")
                except:
                    time_str = start
                    
                real_itinerary[day_str].append({
                    "id": f"real-act-{day}-{len(real_itinerary[day_str])}",
                    "title": item.get("activity", "Activity"),
                    "time": time_str,
                    "duration": f"{item.get('start_time', '')} - {item.get('end_time', '')}",
                    "category": item.get("category", "Sightseeing"),
                    "rating": 4.5,
                    "entryFee": "See Notes",
                    "description": item.get("notes", ""),
                    "location": item.get("location", ""),
                    "image": trip_service._get_image_for_category(item.get("category", "Sightseeing"), g_state.get("destination", "Unknown"))
                })
        except Exception as e:
            print(f"Error building real itinerary: {e}")

    if real_itinerary:
        city = g_state.get("destination", "Unknown")
        days = int(g_state.get("days", 3))
        budget = g_state.get("budget", "Moderate")
        travel_style = g_state.get("travel_style", "Cultural")
        trip_id = g_state.get("trip_id", "draft-trip")
        
        # Enrich dynamic sections
        packing_tips = PackingService.get_packing_tips(city, travel_style, budget)
        packing_checklist = PackingService.get_packing_checklist(city, travel_style, budget)
        budget_summary = BudgetService.calculate_budget_summary(city, days, budget)
        emergency_contacts = EmergencyService.get_emergency_contacts(city)
        hotels = trip_service.get_structured_hotels(city, budget)
        restaurants = trip_service.get_structured_restaurants(city, budget)
        
        trip_response = {
            "trip_id": trip_id,
            "city": city.title(),
            "duration": days,
            "budget": budget,
            "travel_style": travel_style,
            "travelers": int(g_state.get("travelers", 1)),
            "weather_summary": budget_summary.get("weather_summary", f"Weather forecast for {city.title()}"),
            "packing": packing_tips,
            "packing_checklist": packing_checklist,
            "emergency": emergency_contacts,
            "budget_summary": budget_summary,
            "hotels": hotels,
            "restaurants": restaurants,
            "itinerary": real_itinerary,
            "calendar": {
                "saved": False,
                "synced": False
            }
        }
        
        return {
            "status": "success",
            "answer": result["answer"],
            "routes": result.get("routes", []),
            "trip": trip_response,
            "metadata": {
                "source": "llm",
                "generated_by": "calendar_agent",
                "cached": False,
                "generated_at": datetime.now().isoformat()
            }
        }

    return {
        "status": "success",
        "answer": result["answer"],
        "routes": result.get("routes", []),
        "trip": None,
        "metadata": {
            "source": "guided_flow",
            "generated_by": "supervisor",
            "cached": False,
            "generated_at": datetime.now().isoformat()
        }
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
            
        ics = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//TouristAI//ItineraryExporter//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH"
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

@app.get("/login/google")
def login_google(trip_id: str):
    gcal_service = GoogleCalendarService()
    if not gcal_service.is_configured():
        return RedirectResponse(f"http://localhost:8000/oauth2callback?code=mock_code&state={trip_id}")
    auth_url = gcal_service.get_authorization_url(trip_id)
    return RedirectResponse(auth_url)

@app.get("/oauth2callback")
def oauth2callback(code: str, state: str):
    trip_id = state
    gcal_service = GoogleCalendarService()
    if gcal_service.is_configured():
        gcal_service.save_credentials_from_code(code)
    
    calendar_service = CalendarService()
    g_state = get_guided_state()
    travel_date = g_state.get("travel_date")
    if not travel_date or travel_date == "None":
        travel_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
    res = calendar_service.sync_to_google_calendar(trip_id, start_date_str=travel_date)
    
    if res.get("success"):
        msg = "Google Calendar has been synchronized with your travel itinerary successfully."
        if not gcal_service.is_configured():
            msg += " (Simulated Mode - Credentials not configured)"
        return HTMLResponse(content=f"""
            <html>
                <head>
                    <title>Authentication Successful</title>
                    <style>
                        body {{ font-family: sans-serif; text-align: center; margin-top: 100px; background-color: #0b0f19; color: #f3f4f6; }}
                        .container {{ max-width: 500px; margin: 0 auto; padding: 40px; background-color: #111827; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); }}
                        h1 {{ color: #10b981; }}
                        p {{ color: #9ca3af; margin-bottom: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>✓ Authentication Successful!</h1>
                        <p>{msg}</p>
                        <p>You can close this tab and return to the chat assistant.</p>
                    </div>
                </body>
            </html>
        """)
    else:
        return HTMLResponse(content=f"<h1>Sync Failed</h1><p>{res.get('message')}</p>")