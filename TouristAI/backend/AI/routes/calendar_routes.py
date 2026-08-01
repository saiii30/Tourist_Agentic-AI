from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from typing import Optional
import json
import traceback
import uuid
from datetime import datetime, timedelta

from pydantic import BaseModel
from typing import List, Dict

from services.google_calendar_service import GoogleCalendarService
from services.calendar_service import CalendarService
from repositories.trip_repository import TripRepository
from models.itinerary import Trip, ItineraryItem
from database.postgres import PostgresDatabase
from supervisor import get_guided_state

router = APIRouter()


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
    travel_time: Optional[str] = None
    transport: Optional[str] = None
    distance: Optional[str] = None


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
    currentLocation: Optional[str] = "None"
    status: str = "SAVED"
    itinerary: Dict[str, List[SaveAndSyncActivity]]
    metadata: Optional[dict] = None


@router.post("/calendar/save")
def save_calendar(req: SaveCalendarRequest):
    from supervisor import save_itinerary_to_db
    return save_itinerary_to_db(req.itinerary_text, req.trip_name)


@router.post("/calendar/save-and-sync")
def save_and_sync(req: SaveAndSyncRequest):
    calendar_service = CalendarService(user_id=req.user_id)
    repo = TripRepository()

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
                google_event_id=item.google_event_id,
                travel_time=item.travel_time,
                transport=item.transport,
                distance=item.distance,
            ))

    existing_items = repo.get_itinerary_items(req.trip_id)
    changed = False
    if len(existing_items) != len(flat_items):
        changed = True
    else:
        sorted_existing = sorted(existing_items, key=lambda x: x.activity_id)
        sorted_new = sorted(flat_items, key=lambda x: x.activity_id)
        for i in range(len(sorted_existing)):
            e, n = sorted_existing[i], sorted_new[i]
            if (e.activity != n.activity or e.day != n.day or e.start_time != n.start_time or e.end_time != n.end_time or e.location != n.location or e.notes != n.notes):
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
        current_location=req.currentLocation,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )

    calendar_service.save_itinerary(trip_obj, flat_items)

    if req.metadata:
        repo.save_trip_details(req.trip_id, req.metadata)

    versions = repo.get_trip_versions(req.trip_id)
    if changed or not versions:
        next_version = versions[0]["version"] + 1 if versions else 1
        snapshot_str = json.dumps([it.dict() for it in flat_items])
        repo.save_trip_version(req.trip_id, next_version, snapshot_str)

    gcal_service = GoogleCalendarService(user_id=req.user_id)
    if not gcal_service.is_configured():
        sync_res = calendar_service.sync_to_google_calendar(req.trip_id, start_date_str=req.travel_date)
        return {"saved": True, "synced": True, "simulated": True, "message": sync_res.get("message")}

    if gcal_service.is_authenticated():
        sync_res = calendar_service.sync_to_google_calendar(req.trip_id, start_date_str=req.travel_date)
        return {"saved": True, "synced": sync_res.get("success", False), "message": sync_res.get("message")}

    auth_url = gcal_service.get_authorization_url(req.trip_id)
    return {"saved": True, "synced": False, "needs_auth": True, "auth_url": auth_url}


@router.get("/calendar/export")
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
            "METHOD:PUBLISH",
        ]
        base_date = datetime.now() + timedelta(days=1)

        for row in rows:
            day_num, time_slot, time_range, activity, details = row
            event_date = base_date + timedelta(days=(day_num - 1))
            date_str = event_date.strftime("%Y%m%d")
            start_hour, end_hour = 9, 12
            if time_slot.lower() == "afternoon":
                start_hour, end_hour = 12, 17
            elif time_slot.lower() == "evening":
                start_hour, end_hour = 17, 21
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
                "END:VEVENT",
            ])

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


@router.get("/trips/{trip_id}")
def get_trip_by_id(trip_id: str):
    repo = TripRepository()
    trip = repo.get_trip(trip_id)
    if not trip:
        return Response(status_code=404)
    return {
        "trip_id": trip.trip_id,
        "city": trip.city,
        "days": trip.days,
        "budget": trip.budget,
        "travel_style": trip.travel_style,
        "travelers": trip.travelers,
        "interests": trip.interests,
        "status": trip.status,
        "travel_date": trip.travel_date,
        "current_location": trip.current_location or "None",
        "created_at": trip.created_at,
        "updated_at": trip.updated_at,
    }


@router.get("/login/google")
def login_google(trip_id: str):
    repo = TripRepository()
    trip = repo.get_trip(trip_id)
    user_id = trip.user_id if trip else "guest_user"
    gcal_service = GoogleCalendarService(user_id=user_id)
    if not gcal_service.is_configured():
        return RedirectResponse(f"http://localhost:8000/oauth2callback?code=mock_code&state={trip_id}")
    auth_url = gcal_service.get_authorization_url(trip_id)
    return RedirectResponse(auth_url)


@router.get("/oauth2callback")
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
            traceback.print_exc()
            return HTMLResponse(content=f"<h1>Authentication Failed</h1><p>Failed to exchange Google OAuth code: {str(e)}</p>", status_code=500)

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

    return HTMLResponse(content=f"""
        <html>
            <head><title>Authentication Successful</title></head>
            <body>
                <h1>Authentication Successful</h1>
                <p>Google Calendar has been authorized successfully.</p>
                <script>
                    if (window.opener) {{ window.opener.postMessage({{ type: 'GOOGLE_AUTH_SUCCESS', trip_id: '{trip_id}' }}, '*'); }}
                    setTimeout(function() {{ window.close(); }}, 1500);
                </script>
            </body>
        </html>
    """)
