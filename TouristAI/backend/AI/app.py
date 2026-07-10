import os
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
from database.postgres import PostgresDatabase
import json
import sys
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Response, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
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
from repositories.trip_repository import TripRepository

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

trip_service = TripService()

class ChatRequest(BaseModel):
    question: str
    user_id: Optional[str] = "guest_user"

class SaveCalendarRequest(BaseModel):
    itinerary_text: str
    trip_name: str = None

class SaveAndSyncActivity(BaseModel):
    activity_id: Optional[str] = None
    day: int
    start_time: str
    end_time: str
    activity: str
    location: str
    category: str
    restaurant: Optional[str] = None
    hotel: Optional[str] = None
    notes: Optional[str] = None
    google_event_id: Optional[str] = None

class SaveAndSyncRequest(BaseModel):
    trip_id: str
    user_id: Optional[str] = "guest_user"
    city: str
    duration: int
    budget: str
    travel_style: str
    travelers: int
    interests: str
    travel_date: str
    status: str = "SAVED"
    itinerary: Dict[str, List[SaveAndSyncActivity]]
    metadata: Optional[dict] = None

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

    # Deactivate guided planning if a new single-topic query is asked, to escape any stuck flow
    is_single_topic = any(kw in question_lower for kw in ["weather", "forecast", "climate", "temperature", "rain", "hotel", "stay", "resort", "restaurant", "food", "eat", "cafe", "attraction", "sightseeing", "places to visit", "things to do"])
    if is_single_topic:
        update_guided_state("is_active", "0")
        
    start_keywords = ["trip", "plan", "itinerary", "vacation", "holiday", "tour", "reset", "start over"]
    is_start = matches_keywords = lambda q, kw: any(k in q for k in kw)
    is_start = is_start(question_lower, start_keywords)
    
    g_state = get_guided_state()
    is_active = g_state.get("is_active") == "1"
    
    if not is_start and not is_active:
        # Only trigger a new trip if trip-related keywords are present, not just a city.
        # This prevents single-topic queries (like for hotels) from starting a full plan.
        from supervisor import extract_query_details, matches_keywords
        details = extract_query_details(req.question)
        if details.get("city") != "None" and details.get("requires_city", True):
            is_start = matches_keywords(question_lower, start_keywords)
            
    if is_start:
        from supervisor import extract_all_opening_details
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
                    "id": item.get("activity_id") or f"real-act-{day}-{len(real_itinerary[day_str])}",
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

    itinerary_routes = {"calendar", "modify_itinerary", "regenerate_itinerary", "save_itinerary", "delete_itinerary", "google_calendar"}
    has_itinerary_route = any(r in itinerary_routes for r in result.get("routes", []))

    if real_itinerary and has_itinerary_route:
        city = g_state.get("destination", "Unknown")
        days = int(g_state.get("days", 3))
        budget = g_state.get("budget", "Moderate")
        travel_style = g_state.get("travel_style", "Cultural")
        trip_id = g_state.get("trip_id", "draft-trip")
        
        # Ensure a valid unique trip ID is registered
        if trip_id == "draft-trip":
            trip_id = str(uuid.uuid4())
            update_guided_state("trip_id", trip_id)
            
        # 1. Parse natural language date using CalendarService parser
        from services.calendar_service import CalendarService
        calendar_service = CalendarService(user_id=req.user_id)
        
        travel_date_raw = g_state.get("travel_date")
        travel_date = None
        if travel_date_raw and travel_date_raw != "None":
            parsed_str = calendar_service._parse_natural_date(travel_date_raw)
            try:
                datetime.strptime(parsed_str.strip(), "%Y-%m-%d")
                travel_date = parsed_str.strip()
            except ValueError:
                pass
                
        if not travel_date:
            travel_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
        # Enrich dynamic sections
        packing_tips = PackingService.get_packing_tips(city, travel_style, budget)
        packing_checklist = PackingService.get_packing_checklist(city, travel_style, budget)
        budget_summary = BudgetService.calculate_budget_summary(city, days, budget)
        emergency_contacts = EmergencyService.get_emergency_contacts(city)
        hotels = trip_service.get_structured_hotels(city, budget)
        restaurants = trip_service.get_structured_restaurants(city, budget)
        
        # 2. Parse JSON list to models.itinerary objects
        from models.itinerary import Trip, ItineraryItem
        
        trip_obj = Trip(
            trip_id=trip_id,
            user_id=req.user_id or "guest_user",
            city=city.title(),
            days=days,
            budget=budget,
            travel_style=travel_style,
            travelers=int(g_state.get("travelers", 1)),
            interests=g_state.get("interests", "None"),
            status="GENERATED",
            travel_date=travel_date,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        itinerary_items = []
        parsed_raw_items = json.loads(last_items)
        for item in parsed_raw_items:
            itinerary_items.append(ItineraryItem(
                trip_id=trip_id,
                day=item.get("day", 1),
                start_time=item.get("start_time", "09:00"),
                end_time=item.get("end_time", "12:00"),
                activity=item.get("activity", "Activity"),
                location=item.get("location", ""),
                category=item.get("category", "Sightseeing"),
                restaurant=item.get("restaurant"),
                hotel=item.get("hotel"),
                notes=item.get("notes"),
                activity_id=item.get("activity_id") or str(uuid.uuid4()),
                google_event_id=item.get("google_event_id")
            ))
            
        # 2. Save items directly back to guided state with assigned IDs
        updated_items_json = json.dumps([item.dict() for item in itinerary_items])
        update_guided_state("last_itinerary_items", updated_items_json)
        
        trip_response = {
            "trip_id": trip_id,
            "city": city.title(),
            "duration": days,
            "budget": budget,
            "travel_date": travel_date,
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

@app.post("/calendar/save-and-sync")
def save_and_sync(req: SaveAndSyncRequest):
    from models.itinerary import Trip, ItineraryItem
    
    calendar_service = CalendarService(user_id=req.user_id)
    repo = TripRepository()
    
    # 1. Flatten Map itinerary to list of ItineraryItem models
    flat_items = []
    for day_str, day_items in req.itinerary.items():
        day = int(day_str)
        for item in day_items:
            flat_items.append(ItineraryItem(
                trip_id=req.trip_id,
                day=day,
                start_time=item.start_time,
                end_time=item.end_time,
                activity=item.activity,
                location=item.location,
                category=item.category,
                restaurant=item.restaurant,
                hotel=item.hotel,
                notes=item.notes,
                activity_id=item.activity_id or str(uuid.uuid4()),
                google_event_id=item.google_event_id
            ))
            
    # 2. Check for modifications to handle version snapshots
    existing_items = repo.get_itinerary_items(req.trip_id)
    changed = False
    if len(existing_items) != len(flat_items):
        changed = True
    else:
        sorted_existing = sorted(existing_items, key=lambda x: x.activity_id)
        sorted_new = sorted(flat_items, key=lambda x: x.activity_id)
        for i in range(len(sorted_existing)):
            e, n = sorted_existing[i], sorted_new[i]
            if (e.activity != n.activity or e.day != n.day or e.start_time != n.start_time or 
                e.end_time != n.end_time or e.location != n.location or e.notes != n.notes):
                changed = True
                break
                
    status = req.status
    if changed:
        status = "MODIFIED"
        
    trip_obj = Trip(
        trip_id=req.trip_id,
        user_id=req.user_id or "guest_user",
        city=req.city,
        days=req.duration,
        budget=req.budget,
        travel_style=req.travel_style,
        travelers=req.travelers,
        interests=req.interests,
        status=status,
        travel_date=req.travel_date,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    # Save the flattened items
    calendar_service.save_itinerary(trip_obj, flat_items)
    
    # Save metadata JSON details
    if req.metadata:
        repo.save_trip_details(req.trip_id, req.metadata)
        
    # Save version snapshot if changed
    versions = repo.get_trip_versions(req.trip_id)
    if changed or not versions:
        next_version = versions[0]["version"] + 1 if versions else 1
        snapshot_str = json.dumps([it.dict() for it in flat_items])
        repo.save_trip_version(req.trip_id, next_version, snapshot_str)
        
    # 3. Handle auth and sync
    gcal_service = GoogleCalendarService(user_id=req.user_id)
    if not gcal_service.is_configured():
        sync_res = calendar_service.sync_to_google_calendar(req.trip_id, start_date_str=req.travel_date)
        return {
            "saved": True,
            "synced": True,
            "simulated": True,
            "message": sync_res.get("message")
        }
        
    if gcal_service.is_authenticated():
        sync_res = calendar_service.sync_to_google_calendar(req.trip_id, start_date_str=req.travel_date)
        return {
            "saved": True,
            "synced": sync_res.get("success", False),
            "message": sync_res.get("message")
        }
    else:
        auth_url = gcal_service.get_authorization_url(req.trip_id)
        return {
            "saved": True,
            "synced": False,
            "needs_auth": True,
            "auth_url": auth_url
        }

@app.get("/calendar/export")
def export_calendar(trip_name: str):
    try:
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.day, 'Morning' as time_slot, '09:00 - 12:00' as time_range, c.activity, c.activity as details
            FROM calendar_events c
            JOIN trips t ON c.trip_id = t.trip_id
            WHERE LOWER(t.city) = LOWER(%s)
            ORDER BY c.day, c.id
        """, (trip_name,))
        rows = cursor.fetchall()
        cursor.close()
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
    repo = TripRepository()
    trip = repo.get_trip(trip_id)
    user_id = trip.user_id if trip else "guest_user"
    
    gcal_service = GoogleCalendarService(user_id=user_id)
    if not gcal_service.is_configured():
        return RedirectResponse(f"http://localhost:8000/oauth2callback?code=mock_code&state={trip_id}")
    auth_url = gcal_service.get_authorization_url(trip_id)
    return RedirectResponse(auth_url)

@app.get("/oauth2callback")
def oauth2callback(code: str, state: str):
    trip_id = state
    repo = TripRepository()
    trip = repo.get_trip(trip_id)
    user_id = trip.user_id if trip else "guest_user"
    
    gcal_service = GoogleCalendarService(user_id=user_id)
    if gcal_service.is_configured():
        try:
            gcal_service.save_credentials_from_code(code, trip_id=trip_id)
        except Exception as e:
            print(f"Error saving credentials in oauth2callback: {e}")
            import traceback
            traceback.print_exc()
            return HTMLResponse(content=f"<h1>Authentication Failed</h1><p>Failed to exchange Google OAuth code: {str(e)}</p>", status_code=500)
    
    # Fail-safe backend fallback: trigger sync immediately in the callback to ensure events are created
    # even if the frontend isn't refreshed or misses the postMessage callback.
    calendar_service = CalendarService(user_id=user_id)
    travel_date = trip.travel_date if trip and trip.travel_date else None
    if not travel_date or travel_date == "None":
        g_state = get_guided_state()
        travel_date = g_state.get("travel_date")
    if not travel_date or travel_date == "None":
        travel_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
    try:
        calendar_service.sync_to_google_calendar(trip_id, start_date_str=travel_date)
    except Exception as e:
        print(f"Error executing fallback sync in oauth2callback: {e}")
    
    # Safe success page containing postMessage callback logic back to React
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
                    <p>Google Calendar has been authorized successfully.</p>
                    <p>Closing window and starting sync...</p>
                </div>
                <script>
                    if (window.opener) {{
                        window.opener.postMessage({{ type: 'GOOGLE_AUTH_SUCCESS', trip_id: '{trip_id}' }}, '*');
                    }}
                    setTimeout(function() {{ window.close(); }}, 1500);
                </script>
            </body>
        </html>
    """)