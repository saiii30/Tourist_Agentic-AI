import os
import sys
import asyncio
import re

AI_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_ROOT = os.path.dirname(AI_ROOT)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
from dotenv import load_dotenv

# Load environment variables from possible locations to ensure API keys are populated
for env_path in [
    os.path.join(AI_ROOT, ".env"),
    os.path.join(BACKEND_ROOT, ".env"),
    os.path.abspath(os.path.join(os.getcwd(), ".env")),
    os.path.abspath(os.path.join(os.getcwd(), "backend", ".env")),
]:
    if os.path.exists(env_path):
        load_dotenv(env_path)
try:
    from ..database.postgres import PostgresDatabase
except (ImportError, ValueError):
    from database.postgres import PostgresDatabase
import json
import sys
import uuid
from urllib.parse import quote
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Response, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
import requests
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware

# Adjust path to import correctly
if AI_ROOT not in sys.path:
    sys.path.append(AI_ROOT)
if BACKEND_ROOT not in sys.path:
    sys.path.append(BACKEND_ROOT)

from services.google_calendar_service import GoogleCalendarService
from services.calendar_service import CalendarService
from services.trip_service import TripService
from services.packing_service import PackingService
from services.budget_service import BudgetService
from services.emergency_service import EmergencyService
from services.live_web_search_service import answer_from_live_web
from supervisor import (
    get_guided_state,
    update_guided_state,
    clear_guided_state,
    extract_all_opening_details,
    extract_query_details,
    matches_keywords
)
from chat_flow import analyze_chat_flow, build_loader_stages
from graph import graph
from repositories.trip_repository import TripRepository
from routes import travel_routes, calendar_routes
from routers.nearby import nearby as nearby_lookup

travel_search_flights = travel_routes.search_flights
travel_search_buses = travel_routes.search_buses
travel_search_stations = travel_routes.search_stations
travel_trains_between = travel_routes.trains_between
travel_optimize_route_endpoint = travel_routes.optimize_route_endpoint
travel_calculate_budget = travel_routes.calculate_budget
travel_get_exchange_rates = travel_routes.get_exchange_rates

calendar_save = calendar_routes.save_calendar
calendar_save_and_sync = calendar_routes.save_and_sync
calendar_export = calendar_routes.export_calendar
calendar_get_trip_by_id = calendar_routes.get_trip_by_id
calendar_login_google = calendar_routes.login_google
calendar_oauth2callback = calendar_routes.oauth2callback

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

trip_service = TripService()


@app.get("/place-photo")
def place_photo(
    photo_name: str = Query(...),
    maxwidth: int = Query(800, ge=1, le=4800),
    maxheight: int = Query(800, ge=1, le=4800),
):
    """Proxy a Google Places photo without sending the API key to the client."""
    if not photo_name.startswith("places/") or "/photos/" not in photo_name:
        return Response(status_code=400)

    photo_resource = photo_name[:-6] if photo_name.endswith("/media") else photo_name

    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        return Response(status_code=503)

    try:
        google_response = requests.get(
            f"https://places.googleapis.com/v1/{photo_resource}/media",
            params={
                "key": api_key,
                "maxWidthPx": maxwidth,
                "maxHeightPx": maxheight,
            },
            timeout=8,
            allow_redirects=False,
        )

        redirect_url = google_response.headers.get("location")
        if google_response.status_code in {301, 302, 303, 307, 308} and redirect_url:
            return RedirectResponse(
                url=redirect_url,
                status_code=302,
                headers={"Cache-Control": "public, max-age=86400"},
            )

        if not google_response.ok or not google_response.headers.get("content-type", "").startswith("image/"):
            return Response(status_code=404)

        return Response(
            content=google_response.content,
            media_type=google_response.headers["content-type"],
            headers={"Cache-Control": "public, max-age=86400"},
        )
    except requests.RequestException:
        return Response(status_code=502)


@app.get("/api/nearby")
async def nearby_api_proxy(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: int = Query(5000, ge=10, le=50000),
    category: List[str] = Query(...),
    open_now: Optional[bool] = Query(None),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    max_price: Optional[int] = Query(None, ge=0),
):
    return await nearby_lookup(
        lat=lat,
        lng=lng,
        radius=radius,
        category=category,
        open_now=open_now,
        min_rating=min_rating,
        max_price=max_price,
    )


def attach_discovery_photo_urls(discovery_result: Optional[dict]) -> None:
    """Use the Google image only when Wikipedia did not supply one."""
    if not isinstance(discovery_result, dict):
        return

    api_base_url = os.getenv("AI_API_PUBLIC_URL", "http://localhost:8000").rstrip("/")
    for category in discovery_result.get("categories") or []:
        for place in category.get("places") or []:
            photo_name = place.get("googlePhotoName")
            if not place.get("image") and photo_name:
                place["image"] = f"{api_base_url}/place-photo?photo_name={quote(photo_name, safe='')}"

def clear_cached_place_agent_data() -> None:
    for key in ("hotels_data", "restaurants_data", "nearby_data"):
        update_guided_state(key, "")

class ChatRequest(BaseModel):
    question: str
    user_id: Optional[str] = "guest_user"
    destination: Optional[str] = None
    city: Optional[str] = None
    days: Optional[int] = None
    budget: Optional[str] = None
    travelers: Optional[int] = None
    travel_style: Optional[str] = None
    interests: Optional[str] = None
    travel_mode: Optional[str] = None
    current_location: Optional[str] = None
    travel_date: Optional[str] = None
    travel_profile: Optional[dict] = None

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

def map_hotels_to_frontend(hotels_data, city_clean):
    frontend_hotels = []
    if not hotels_data:
        return frontend_hotels
    for idx, h in enumerate(hotels_data):
        price_val = h.get("pricePerNight") or h.get("price") or 3000
        hotel_photos = h.get("photos") or []
        first_hotel_photo = hotel_photos[0] if hotel_photos else None
        try:
            if isinstance(price_val, str):
                import re
                digits = re.findall(r'\d+', price_val.replace(",", ""))
                price_val = int(digits[0]) if digits else 3000
            price_val = int(price_val)
        except:
            price_val = 3000
            
        frontend_hotels.append({
            "id": h.get("hotel_id") or f"hotel-{idx}",
            "name": h.get("name", "N/A"),
            "image": h.get("image") or first_hotel_photo or "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Indian_hotel.jpg/400px-Indian_hotel.jpg",
            "photos": hotel_photos,
            "googlePhotoName": h.get("googlePhotoName") or h.get("google_photo_name"),
            "rating": h.get("rating") or 4.5,
            "reviews": h.get("reviews") or h.get("userRatingCount") or 0,
            "pricePerNight": price_val,
            "amenities": h.get("amenities") or ["Free Wi-Fi", "Room Service"],
            "hotelType": h.get("hotel_type") or h.get("type"),
            "roomTypes": h.get("room_types") or [],
            "parking": h.get("parking"),
            "distanceFromCenter": h.get("address", "Central Location"),
            "bookingUrl": h.get("booking_url") or h.get("website") or "https://booking.com",
            "latitude": h.get("latitude") or h.get("lat"),
            "longitude": h.get("longitude") or h.get("lng")
        })
    return frontend_hotels

def map_restaurants_to_frontend(restaurants_data):
    frontend_rests = []
    if not restaurants_data:
        return frontend_rests
    for idx, r in enumerate(restaurants_data):
        price_tier = "$$"
        p = str(r.get("price", ""))
        if p:
            if "very_expensive" in p.lower() or "expensive" in p.lower() or "high" in p.lower():
                price_tier = "$$$$"
            elif "moderate" in p.lower() or "medium" in p.lower():
                price_tier = "$$$"
            elif "inexpensive" in p.lower() or "cheap" in p.lower() or "low" in p.lower():
                price_tier = "$"
        rest_photos = r.get("photos") or []
        first_rest_photo = rest_photos[0] if rest_photos else None
        dining_options = []
        if r.get("serves_breakfast"):
            dining_options.append("Breakfast")
        if r.get("serves_lunch"):
            dining_options.append("Lunch")
        if r.get("serves_dinner"):
            dining_options.append("Dinner")
        if r.get("serves_vegetarian"):
            dining_options.append("Vegetarian")
                
        frontend_rests.append({
            "id": r.get("restaurant_id") or f"rest-{idx}",
            "name": r.get("name", "N/A"),
            "image": r.get("image") or first_rest_photo or "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Indian_dinner.jpg/400px-Indian_dinner.jpg",
            "photos": rest_photos,
            "googlePhotoName": r.get("googlePhotoName") or r.get("google_photo_name"),
            "rating": r.get("rating") or 4.5,
            "reviews": r.get("reviews") or r.get("userRatingCount") or 0,
            "cuisine": "Local & Multi-cuisine" if not r.get("serves_vegetarian") else "Vegetarian / Indian",
            "priceTier": price_tier,
            "distanceFromHotel": r.get("distanceFromHotel") or r.get("address") or "0.5 km",
            "reservationAvailable": idx % 2 == 0,
            "address": r.get("address"),
            "website": r.get("website"),
            "mapsUrl": r.get("mapsUrl") or r.get("googleMapsUri"),
            "phone": r.get("phone") or r.get("nationalPhoneNumber") or r.get("internationalPhoneNumber"),
            "hours": r.get("hours") or [],
            "diningOptions": dining_options,
            "servesVegetarian": bool(r.get("serves_vegetarian")),
            "servesBreakfast": bool(r.get("serves_breakfast")),
            "servesLunch": bool(r.get("serves_lunch")),
            "servesDinner": bool(r.get("serves_dinner")),
            "takeout": bool(r.get("takeout")),
            "delivery": bool(r.get("delivery")),
            "dineIn": bool(r.get("dineIn")),
            "goodForChildren": bool(r.get("goodForChildren")),
            "goodForGroups": bool(r.get("goodForGroups")),
            "allowsDogs": bool(r.get("allowsDogs")),
            "accessibility": r.get("accessibility") or r.get("accessibilityOptions") or {},
            "parking": r.get("parking") or r.get("parkingOptions") or {},
            "summary": r.get("summary") or r.get("editorialSummary"),
            "latitude": r.get("latitude") or r.get("lat"),
            "longitude": r.get("longitude") or r.get("lng")
        })
    return frontend_rests

@app.post("/chat")
def chat(req: ChatRequest):
    question_lower = req.question.strip().lower()
    profile = req.travel_profile if isinstance(req.travel_profile, dict) else {}

    def first_real(*values, default="None"):
        for value in values:
            if value is None:
                continue
            if isinstance(value, str):
                stripped = value.strip()
                if stripped and stripped.lower() != "none":
                    return stripped
            elif value != []:
                return value
        return default

    def profile_value(*keys):
        for key in keys:
            value = profile.get(key)
            if value not in (None, "", "None", []):
                return value
        return None

    def profile_list_text(key):
        value = profile_value(key)
        if isinstance(value, list):
            return ", ".join(str(item) for item in value if item)
        return value

    def traveler_count(value, fallback=1):
        try:
            digits = "".join(ch for ch in str(value) if ch.isdigit())
            return int(digits) if digits else fallback
        except Exception:
            return fallback

    print(
        "[LOG][CHAT_REQUEST] "
        f"question={req.question!r}, city={req.city or req.destination or 'None'}, "
        f"days={req.days or 'None'}, budget={req.budget or 'None'}, travelers={req.travelers or 'None'}, "
        f"style={req.travel_style or 'None'}, interests={req.interests or 'None'}, "
        f"mode={req.travel_mode or 'None'}"
    )
    if question_lower == "exit":
        from supervisor import init_guided_db
        init_guided_db()
        from database.postgres import PostgresDatabase
        conn = PostgresDatabase.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE agent_sessions SET status = 'CANCELLED' WHERE status = 'ACTIVE' OR status = 'PAUSED'")
        cursor.execute("DELETE FROM agent_session_state")
        conn.commit()
        cursor.close()
        conn.close()

        # Reset all hotel fields to None
        for field in ["city", "checkin", "checkout", "guests", "budget", "breakfast", "amenities"]:
            update_guided_state(f"hotel.{field}", "None")
        update_guided_state("active_agent", "")
        update_guided_state("is_active", "0")
        update_guided_state("last_completed_agent", "")
        return {
            "status": "success",
            "answer": "Exited hotel search flow.",
            "routes": ["general"]
        }

    g_state = get_guided_state()
    is_active_before_plan = g_state.get("is_active") == "1" or g_state.get("agent_flow_active") == "1"
    flow_plan = analyze_chat_flow(req.question, active_flow=is_active_before_plan)
    print(
        "[LOG][CHAT_FLOW] "
        f"intent={flow_plan.intent}, confidence={flow_plan.confidence:.2f}, "
        f"destination={flow_plan.destination or 'None'}, direct_rag={flow_plan.should_use_direct_rag}, "
        f"start_trip={flow_plan.should_start_trip}, reset_questionnaire={flow_plan.should_reset_questionnaire}, "
        f"reason={flow_plan.reason}"
    )

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

    # 0. Direct trusted-knowledge query before the graph can start questionnaires.
    if flow_plan.should_use_direct_rag:
        rag_error = None
        rag_res = {}
        city_for_rag = req.destination or req.city or flow_plan.destination or g_state.get("destination") or "Madurai"
        try:
            from rag.service import rag_service
            rag_res = rag_service.query_rag(req.question, agent_name="GeneralAgent", city=city_for_rag)
            if rag_res.get("has_knowledge") and rag_res.get("context_text"):
                rag_answer = rag_res.get("answer_text") or rag_res["context_text"]
                cites = rag_res.get("citations", [])
                cite_str = ""
                if cites:
                    cite_str = "\n\n**Verified RAG Sources**:\n" + "\n".join([f"- [{c['source_name']}]({c['source_url']}) ({c['trust_score']})" for c in cites])
                
                return {
                    "status": "success",
                    "answer": f"**RAG Knowledge Answer**\n\n{rag_answer}{cite_str}",
                    "routes": ["rag_service"],
                    "trip": None,
                    "metadata": {
                        "source": "rag_service",
                        "generated_by": "rag_knowledge_service",
                        "cached": False,
                        "image_url": rag_res.get("image_url"),
                        "image_urls": rag_res.get("image_urls"),
                        "chat_flow": {
                            "intent": flow_plan.intent,
                            "confidence": flow_plan.confidence,
                            "entities": flow_plan.entities,
                            "reason": flow_plan.reason,
                        },
                        "generated_at": datetime.now().isoformat()
                    }
                }
        except Exception as e:
            rag_error = str(e)
            print(f"Error handling direct RAG query: {e}")

        try:
            web_res = answer_from_live_web(req.question, destination=city_for_rag)
            if web_res.get("has_answer"):
                sources = web_res.get("sources", [])
                source_lines = "\n".join(
                    f"- [{source['title']}]({source['url']})"
                    for source in sources[:4]
                )
                source_block = f"\n\n**Live Web Sources**:\n{source_lines}" if source_lines else ""
                return {
                    "status": "success",
                    "answer": (
                        "**Live Web Search Answer**\n\n"
                        "I could not find a verified RAG match, so I checked live web results.\n\n"
                        f"{web_res['answer']}{source_block}"
                    ),
                    "routes": ["rag_service", "live_web_search"],
                    "trip": None,
                    "metadata": {
                        "source": "live_web_search",
                        "generated_by": "live_web_search_service",
                        "cached": False,
                        "rag_status": "unavailable" if rag_error else (rag_res.get("coverage_status") or "no_match"),
                        "search_query": web_res.get("search_query"),
                        "web_search_errors": web_res.get("errors", []),
                        "chat_flow": {
                            "intent": flow_plan.intent,
                            "confidence": flow_plan.confidence,
                            "entities": flow_plan.entities,
                            "reason": flow_plan.reason,
                        },
                        "generated_at": datetime.now().isoformat()
                    }
                }
            web_error = web_res.get("error")
        except Exception as e:
            web_error = str(e)
            print(f"Error handling live web fallback: {e}")

        rag_detail = (
            f"Technical detail: `{rag_error}`"
            if rag_error
            else rag_res.get("coverage_message") or "The RAG index loaded, but it did not return a matching verified chunk for this question."
        )
        web_detail = (
            f"Live web search was attempted, but it did not return a usable result. Detail: `{web_error}`"
            if locals().get("web_error")
            else "Live web search was attempted, but it did not return a usable result."
        )
        details = (
            f"\n\n{rag_detail}"
            f"\n\n{web_detail}"
        )
        return {
            "status": "success",
            "answer": (
                "**RAG Knowledge Check**\n\n"
                "I recognized this as a knowledge-base question, but I could not find verified indexed RAG knowledge for it."
                f"{details}"
            ),
            "routes": ["rag_service"],
            "trip": None,
            "metadata": {
                "source": "rag_service",
                "generated_by": "rag_knowledge_service",
                "cached": False,
                "rag_status": "unavailable" if rag_error else "no_match",
                "chat_flow": {
                    "intent": flow_plan.intent,
                    "confidence": flow_plan.confidence,
                    "entities": flow_plan.entities,
                    "reason": flow_plan.reason,
                },
                "generated_at": datetime.now().isoformat()
            }
        }

    # Deactivate guided planning if a new single-topic query is asked, to escape any stuck flow
    is_single_topic = flow_plan.intent in {"hotel", "restaurant", "weather", "transport"} or any(kw in question_lower for kw in ["attraction", "sightseeing", "places to visit", "things to do"])
    if is_single_topic:
        update_guided_state("is_active", "0")
        update_guided_state("last_itinerary_items", "")
        update_guided_state("last_itinerary", "")
        update_guided_state("trip_id", "")
        update_guided_state("trip_status", "")
        clear_cached_place_agent_data()
        
    start_keywords = ["trip", "plan", "itinerary", "vacation", "holiday", "tour", "reset", "start over"]
    is_start = matches_keywords = lambda q, kw: any(k in q for k in kw)
    is_start = flow_plan.should_start_trip or is_start(question_lower, start_keywords)
    
    g_state = get_guided_state()
    is_active = g_state.get("is_active") == "1" or g_state.get("agent_flow_active") == "1"
    print(
        "[LOG][CHAT_MODE] "
        f"is_start={is_start}, is_active={is_active}, active_agent={g_state.get('active_agent') or 'none'}, "
        f"trip_status={g_state.get('trip_status') or 'none'}"
    )
    
    if not is_start and not is_active:
        # Only trigger a new trip if trip-related keywords are present, not just a city.
        # This prevents single-topic queries (like for hotels) from starting a full plan.
        details = extract_query_details(req.question)
        if details.get("city") != "None" and details.get("requires_city", True):
            is_start = matches_keywords(question_lower, start_keywords)
            
    city = "None"
    days_str = "None"
    budget = "None"
    travel_style = "None"
    profile_budget = profile_value("budgetType")
    profile_style = profile_list_text("favoriteTravelStyles")
    profile_transport = profile_value("preferredTransport")
    profile_home = profile_value("homeCity")
    profile_food = profile_value("preferredFood")
    profile_hotel = profile_value("preferredHotel")
    profile_companion = profile_value("companionType")
    profile_group = profile_value("averageGroupSize")

    if is_start:
        clear_guided_state()
        extracted = extract_all_opening_details(req.question)
        city = first_real(req.destination, req.city, flow_plan.destination, extracted.get("destination"), extracted.get("city"))
        days_str = str(first_real(req.days, flow_plan.entities.get("days"), extracted.get("days")))
        budget = first_real(flow_plan.entities.get("budget"), extracted.get("budget"), req.budget, profile_budget)
        travel_style = first_real(extracted.get("travel_style"), req.travel_style, profile_style)
        print(
            "[LOG][CHAT_EXTRACTED] "
            f"city={city}, days={days_str}, budget={budget}, style={travel_style}, "
            f"mode={first_real(extracted.get('travel_mode'), req.travel_mode, profile_transport)}, current_location={first_real(extracted.get('current_location'), req.current_location, profile_home)}, "
            f"date={req.travel_date or extracted.get('travel_date', 'None')}"
        )
        
        for k, v in extracted.items():
            if v and v != "None":
                update_guided_state(k, str(v))
                update_guided_state(f"calendar.{k}", str(v))

        if city and city != "None":
            update_guided_state("destination", city)
            update_guided_state("city", city)
            update_guided_state("calendar.destination", city)
        if days_str and days_str != "None":
            update_guided_state("days", days_str)
            update_guided_state("calendar.days", days_str)
        if budget and budget != "None":
            update_guided_state("budget", budget)
            update_guided_state("calendar.budget", budget)
        travelers_val = first_real(req.travelers, flow_plan.entities.get("travelers"), profile_group, default=None)
        if travelers_val:
            update_guided_state("travelers", str(travelers_val))
            update_guided_state("calendar.travelers", str(travelers_val))
        if travel_style and travel_style != "None":
            update_guided_state("travel_style", travel_style)
            update_guided_state("calendar.travel_style", travel_style)
        interests_val = first_real(req.interests, profile_style, default=None)
        if interests_val:
            update_guided_state("interests", interests_val)
            update_guided_state("calendar.interests", interests_val)
            
        mode_val = first_real(extracted.get("travel_mode"), req.travel_mode, profile_transport, "Flight")
        update_guided_state("travel_mode", mode_val)
        update_guided_state("calendar.travel_mode", mode_val)

        loc_val = first_real(extracted.get("current_location"), req.current_location, profile_home, "Chennai")
        update_guided_state("current_location", loc_val)
        update_guided_state("calendar.current_location", loc_val)

        if req.travel_date and req.travel_date != "None":
            update_guided_state("travel_date", req.travel_date)
            update_guided_state("calendar.travel_date", req.travel_date)

        # Set default travelers & interests for direct widget requests to bypass questionnaire prompts
        if (req.destination or req.city) and req.days:
            c_dest = req.destination or req.city
            c_days = str(req.days)
            c_budget = req.budget or profile_budget or "Moderate"
            c_style = req.travel_style or profile_style or "Cultural"
            c_mode = req.travel_mode or profile_transport or "Flight"
            c_loc = req.current_location if (req.current_location and req.current_location != "None") else (profile_home or "Chennai")
            c_date = req.travel_date if (req.travel_date and req.travel_date != "None") else (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            c_travelers = req.travelers or traveler_count(profile_group, 1)
            c_interests = req.interests or profile_style or "Any"

            for agent_prefix in ["", "calendar."]:
                update_guided_state(f"{agent_prefix}destination", c_dest)
                update_guided_state(f"{agent_prefix}days", c_days)
                update_guided_state(f"{agent_prefix}budget", c_budget)
                update_guided_state(f"{agent_prefix}travel_style", c_style)
                update_guided_state(f"{agent_prefix}travel_mode", c_mode)
                update_guided_state(f"{agent_prefix}current_location", c_loc)
                update_guided_state(f"{agent_prefix}travel_date", c_date)
                update_guided_state(f"{agent_prefix}travelers", str(c_travelers))
                update_guided_state(f"{agent_prefix}interests", c_interests)

            update_guided_state("agent_flow_active", "0")
            update_guided_state("active_agent", "")
            print(
                "[LOG][GUIDED_STATE_SEEDED] "
                f"source=direct_widget, destination={c_dest}, days={c_days}, budget={c_budget}, "
                f"style={c_style}, mode={c_mode}, current_location={c_loc}, date={c_date}, travelers={c_travelers}"
            )

    start_city = (city if is_start and city != "None" else None)
    init_city = start_city or req.city or req.destination or "None"
    init_dest = start_city or req.destination or req.city or "None"
    graph_payload = {
        "question": req.question,
        "responses": [],
        "city": init_city,
        "destination": init_dest,
        "days": (int(days_str) if is_start and days_str.isdigit() else None) or req.days or 3,
        "budget": (budget if is_start and budget != "None" else None) or req.budget or profile_budget or "None",
        "travelers": traveler_count(first_real(req.travelers, profile_group, 1, default=1)),
        "travel_style": (travel_style if is_start and travel_style != "None" else None) or req.travel_style or profile_style or "None",
        "travel_mode": req.travel_mode or profile_transport or "Flight",
        "current_location": req.current_location or profile_home or "Chennai",
        "travel_date": req.travel_date or "None",
        "interests": req.interests or profile_style or "None",
        "breakfast": "None",
        "hotel_type": profile_hotel or "None",
        "amenities": "None",
        "budget_per_person": "None",
        "diet": profile_food or "None",
        "cuisine": "None",
        "meal_time": "None",
        "family_friendly": "None",
        "outdoor_seating": "None",
        "allergies": "None",
        "max_distance": "None",
        "price_preference": "None",
        "traveler_type": profile_companion or "None",
        "include_hotel": "Yes",
        "include_transport": "Yes",
        "shopping_budget": "Yes"
    }
    print(
        "[LOG][GRAPH_INVOKE] "
        f"city={graph_payload['city']}, destination={graph_payload['destination']}, days={graph_payload['days']}, "
        f"budget={graph_payload['budget']}, style={graph_payload['travel_style']}, mode={graph_payload['travel_mode']}, "
        f"current_location={graph_payload['current_location']}, date={graph_payload['travel_date']}, interests={graph_payload['interests']}"
    )

    # 2. Cache Miss: Run LangGraph pipeline
    result = graph.invoke(graph_payload)
    attach_discovery_photo_urls(result.get("nearbyResult"))
    
    g_state = get_guided_state()
    res_dict = result if isinstance(result, dict) else {}
    routes = res_dict.get("routes", [])
    print(
        "[LOG][GRAPH_RESULT] "
        f"routes={routes}, responses={len(res_dict.get('responses') or [])}, "
        f"hotels={len(res_dict.get('hotels_data') or [])}, restaurants={len(res_dict.get('restaurants_data') or [])}, "
        f"attractions={len(res_dict.get('nearby_data') or [])}, transport={len(res_dict.get('transport_data') or [])}, "
        f"notifications={len(res_dict.get('notifications') or [])}"
    )
    active_agent = g_state.get("active_agent")
    is_questionnaire_active = active_agent and g_state.get("agent_flow_active") == "1"

    if is_questionnaire_active and "merge" in routes:
        ans_text = res_dict.get("answer")
        if not ans_text:
            responses = res_dict.get("responses")
            ans_text = str(responses[-1]) if isinstance(responses, list) and responses else "Please answer the next trip question."

        from services.questionnaire_service import get_progress_metadata
        print(
            "[LOG][CHAT_QUESTIONNAIRE_RESPONSE] "
            f"active_agent={active_agent}, routes={routes}, answer_chars={len(ans_text or '')}"
        )
        return {
            "status": "success",
            "answer": ans_text,
            "routes": routes,
            "trip": None,
            "questionnaire": get_progress_metadata(active_agent, g_state),
            "nearbyResult": res_dict.get("nearbyResult"),
            "metadata": {
                "source": "guided_flow",
                "generated_by": "supervisor",
                "cached": False,
                "chat_flow": {
                    "intent": flow_plan.intent,
                    "confidence": flow_plan.confidence,
                    "entities": flow_plan.entities,
                    "reason": flow_plan.reason,
                },
                "generated_at": datetime.now().isoformat()
            }
        }
    
    city = g_state.get("destination", "Unknown")
    budget = g_state.get("budget", "Moderate")
    days_val = int(g_state.get("days", 3)) if str(g_state.get("days", "")).isdigit() else 3
    travel_style_val = g_state.get("travel_style", "Cultural")
    def load_cached_list(key: str):
        try:
            raw = g_state.get(key)
            data = json.loads(raw) if isinstance(raw, str) else raw
            return data if isinstance(data, list) else None
        except Exception:
            return None

    g_hotels = result.get("hotels_data") or load_cached_list("hotels_data")
    g_restaurants = result.get("restaurants_data") or load_cached_list("restaurants_data")
    g_nearby_cached = result.get("nearby_data") or load_cached_list("nearby_data")
    
    if g_hotels:
        hotels = map_hotels_to_frontend(g_hotels, city)
    else:
        hotels = trip_service.get_structured_hotels(city, budget)
        
    if g_restaurants:
        restaurants = map_restaurants_to_frontend(g_restaurants)
    else:
        restaurants = trip_service.get_structured_restaurants(city, budget)

    last_items = g_state.get("last_itinerary_items")
    if (
        not is_questionnaire_active
        and (not last_items or last_items == "[]")
        and city
        and city.lower() != "unknown"
        and city.lower() != "none"
    ):
        try:
            from agents.calendar_agent import calendar_agent
            calendar_text = calendar_agent(
                question=req.question,
                city=city,
                days=days_val,
                interests=g_state.get("interests", "Any"),
                travel_style=travel_style_val,
                budget=budget,
                hotels_data=g_hotels,
                restaurants_data=g_restaurants,
                nearby_data=g_nearby_cached,
                weather_data=result.get("weather_data"),
                transport_data=result.get("transport_data"),
            )
            if calendar_text and "[" in calendar_text and "]" in calendar_text:
                cleaned_items = calendar_text[calendar_text.find("["):calendar_text.rfind("]") + 1]
                update_guided_state("last_itinerary_items", cleaned_items)
            g_state = get_guided_state()
            last_items = g_state.get("last_itinerary_items")
        except Exception as e:
            print(f"Error calling fallback calendar_agent: {e}")

    real_itinerary = None
    
    if last_items and last_items != "[]":
        try:
            items = json.loads(last_items)
            real_itinerary = {}
            
            # Build flat list of attractions from nearby_data or nearbyResult
            g_nearby = g_nearby_cached
            flat_attractions = []
            if g_nearby and isinstance(g_nearby, list):
                for p in g_nearby:
                    img = p.get("image")
                    if not img:
                        photo_name = p.get("googlePhotoName") or p.get("photo_reference")
                        if photo_name:
                            img = f"/place-photo?photo_name={quote(str(photo_name), safe='')}"
                        else:
                            img = trip_service._get_image_for_category("Sightseeing", city.title())
                    flat_attractions.append({
                        "id": p.get("attraction_id") or p.get("id") or f"att-{uuid.uuid4().hex[:6]}",
                        "name": p.get("name"),
                        "address": p.get("address") or f"{city.title()} Sightseeing",
                        "rating": p.get("rating") if isinstance(p.get("rating"), (int, float)) else 4.5,
                        "ratingCount": p.get("reviews") or 500,
                        "description": p.get("editorial") or p.get("description") or f"Famous tourist attraction in {city.title()}.",
                        "image": img,
                        "googlePhotoName": p.get("googlePhotoName"),
                        "categoryKey": p.get("categoryKey") or ((p.get("types") or [None])[0]),
                        "categoryLabel": p.get("categoryLabel"),
                        "types": p.get("types") or [],
                        "mapsUrl": p.get("mapsUrl"),
                        "wikiUrl": p.get("wikiUrl"),
                        "hours": p.get("hours") or [],
                        "accessibility": p.get("accessibility") or {},
                        "parking": p.get("parking") or {},
                        "latitude": p.get("latitude"),
                        "longitude": p.get("longitude"),
                        "website": p.get("website")
                    })
            elif result.get("nearbyResult") and isinstance(result["nearbyResult"], dict):
                for cat in result["nearbyResult"].get("categories", []):
                    for p in cat.get("places", []):
                        img = p.get("image")
                        if not img:
                            photo_name = p.get("googlePhotoName") or p.get("photo_reference")
                            if photo_name:
                                img = f"/place-photo?photo_name={quote(str(photo_name), safe='')}"
                            else:
                                img = trip_service._get_image_for_category("Sightseeing", city.title())
                        flat_attractions.append({
                            "id": p.get("id") or f"att-{uuid.uuid4().hex[:6]}",
                            "name": p.get("name"),
                            "address": p.get("address") or f"{city.title()} Sightseeing",
                            "rating": p.get("rating") if isinstance(p.get("rating"), (int, float)) else 4.5,
                            "ratingCount": p.get("ratingCount") or 500,
                            "description": p.get("description") or f"Famous tourist attraction in {city.title()}.",
                            "image": img,
                            "categoryKey": cat.get("key"),
                            "categoryLabel": cat.get("label"),
                            "mapsUrl": p.get("mapsUrl"),
                            "wikiUrl": p.get("wikiUrl"),
                            "hours": p.get("hours") or [],
                            "latitude": p.get("latitude"),
                            "longitude": p.get("longitude"),
                            "website": p.get("website"),
                            "googlePhotoName": p.get("googlePhotoName")
                        })
                        
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
                    
                # Match title to find the specific image
                activity_title = item.get("activity", "")
                real_image = None
                google_photo_name = item.get("googlePhotoName") or item.get("photo_reference")
                
                for h in hotels:
                    if h.get("name", "").lower() in activity_title.lower() or activity_title.lower() in h.get("name", "").lower():
                        real_image = h.get("image")
                        google_photo_name = google_photo_name or h.get("googlePhotoName") or h.get("photo_reference")
                        break
                
                if not real_image:
                    for r in restaurants:
                        if r.get("name", "").lower() in activity_title.lower() or activity_title.lower() in r.get("name", "").lower():
                            real_image = r.get("image")
                            google_photo_name = google_photo_name or r.get("googlePhotoName") or r.get("photo_reference")
                            break
                            
                if not real_image:
                    for p in flat_attractions:
                        if p.get("name", "").lower() in activity_title.lower() or activity_title.lower() in p.get("name", "").lower():
                            g_photo = p.get("googlePhotoName")
                            google_photo_name = google_photo_name or g_photo
                            if g_photo:
                                real_image = f"/place-photo?photo_name={quote(g_photo, safe='')}&maxwidth=800&maxheight=800"
                            else:
                                real_image = p.get("image")
                            break
                            
                if not real_image:
                    real_image = trip_service._get_image_for_category(item.get("category", "Sightseeing"), g_state.get("destination", "Unknown"))
                
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
                    "image": real_image,
                    "googlePhotoName": google_photo_name,
                    "travel_time": item.get("travel_time"),
                    "transport": item.get("transport"),
                    "distance": item.get("distance"),
                    "travel": {
                        "mode": item.get("transport"),
                        "duration": item.get("travel_time"),
                        "distance": item.get("distance")
                    },
                    "hotel_id": item.get("hotel_id"),
                    "restaurant_id": item.get("restaurant_id"),
                    "attraction_id": item.get("attraction_id")
                })
        except Exception as e:
            print(f"Error building real itinerary: {e}")

    itinerary_routes = {"calendar", "calendar_preview", "modify_itinerary", "regenerate_itinerary", "save_itinerary", "delete_itinerary", "google_calendar"}
    has_itinerary_route = any(r in itinerary_routes for r in result.get("routes", []))

    if real_itinerary:
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
        weather_intelligence = {}
        budget_summary = BudgetService.calculate_budget_summary(city, days_val, budget)
        emergency_contacts = EmergencyService.get_emergency_contacts(city)
        # Hotels and restaurants are pre-loaded above
        
        # 2. Parse JSON list to models.itinerary objects
        from models.itinerary import Trip, ItineraryItem
        
        trip_obj = Trip(
            trip_id=trip_id,
            user_id=req.user_id or "guest_user",
            city=city.title(),
            days=days_val,
            budget=budget,
            travel_style=travel_style,
            travelers=int(g_state.get("travelers", 1)),
            interests=g_state.get("interests", "None"),
            status="GENERATED",
            travel_date=travel_date,
            current_location=g_state.get("current_location", "None"),
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
                google_event_id=item.get("google_event_id"),
                hotel_id=item.get("hotel_id"),
                restaurant_id=item.get("restaurant_id"),
                attraction_id=item.get("attraction_id"),
                travel_time=item.get("travel_time"),
                transport=item.get("transport"),
                distance=item.get("distance")
            ))
            
        # 2. Save items directly back to guided state with assigned IDs
        updated_items_json = json.dumps([item.dict() for item in itinerary_items])
        update_guided_state("last_itinerary_items", updated_items_json)
        
        # Get weather summary from agent responses
        weather_summary = f"Weather forecast for {city.title()}"
        weather_data = result.get("weather_data")
        if weather_data and isinstance(weather_data, dict) and "temp" in weather_data:
            temp = weather_data.get("temp")
            desc = weather_data.get("description", "clear sky")
            weather_summary = f"Currently in {city.title()}, the weather is {temp}°C with {desc}."
            weather_intelligence = weather_data.get("weather_intelligence") or {}
            weather_packing = weather_data.get("packing") or []
            if weather_packing:
                existing_names = {str(item.get("name", "")).lower() for item in packing_checklist if isinstance(item, dict)}
                for item in weather_packing:
                    item_name = str(item)
                    if item_name.lower() not in existing_names:
                        packing_checklist.append({
                            "id": f"weather-pack-{uuid.uuid4().hex[:6]}",
                            "name": item_name,
                            "checked": False,
                        })
                        existing_names.add(item_name.lower())
                packing_tips = list(dict.fromkeys([*packing_tips, *[f"Weather: pack {item}" for item in weather_packing[:4]]]))
        elif result.get("responses"):
            for resp in result["responses"]:
                if resp.startswith("Weather:\n"):
                    weather_summary = resp.split(":\n", 1)[1].strip()
                    break

        trip_response = {
            "trip_id": trip_id,
            "city": city.title(),
            "duration": days_val,
            "budget": budget,
            "travel_date": travel_date,
            "travel_style": travel_style,
            "interests": g_state.get("interests", "None"),
            "travelers": int(g_state.get("travelers", 1)),
            "current_location": g_state.get("current_location", "None"),
            "weather_summary": weather_summary,
            "weather_intelligence": weather_intelligence,
            "packing": packing_tips,
            "packing_checklist": packing_checklist,
            "emergency": emergency_contacts,
            "budget_summary": budget_summary,
            "hotels": hotels,
            "restaurants": restaurants,
            "attractions": flat_attractions,
            "discoveredPlaces": flat_attractions,
            "itinerary": real_itinerary,
            "tickets": result.get("transport_data") or (json.loads(g_state.get("transport_data")) if g_state.get("transport_data") else []),
            "transport_status": result.get("transport_status") or (json.loads(g_state.get("transport_status")) if g_state.get("transport_status") else {"status": "success", "reason": ""}),
            "calendar": {
                "saved": False,
                "synced": False
            }
        }
        # Get notifications from graph execution result
        notifications = result.get("notifications", [])
        trip_response["notifications"] = notifications
        print(
            "[LOG][CHAT_TRIP_RESPONSE] "
            f"trip_id={trip_id}, city={trip_response['city']}, days={trip_response['duration']}, "
            f"hotels={len(trip_response.get('hotels') or [])}, "
            f"restaurants={len(trip_response.get('restaurants') or [])}, "
            f"attractions={len(trip_response.get('attractions') or [])}, "
            f"itinerary_days={len(trip_response.get('itinerary') or {})}, "
            f"tickets={len(trip_response.get('tickets') or [])}, "
            f"notifications={len(notifications or [])}"
        )
        
        res_dict = result if isinstance(result, dict) else {}
        response_data = {
            "status": "success",
            "answer": res_dict.get("answer") or "Here is your generated trip plan.",
            "routes": res_dict.get("routes", []),
            "trip": trip_response,
            "notifications": notifications,
            "nearbyResult": res_dict.get("nearbyResult"), #newly added code for nearbyagent single line 429
            "metadata": {
                "source": "llm",
                "generated_by": "calendar_agent",
                "cached": False,
                "chat_flow": {
                    "intent": flow_plan.intent,
                    "confidence": flow_plan.confidence,
                    "entities": flow_plan.entities,
                    "reason": flow_plan.reason,
                },
                "generated_at": datetime.now().isoformat()
            }
        }
        g_state = get_guided_state()
        active_agent = g_state.get("active_agent")
        if active_agent and g_state.get("agent_flow_active") == "1":
            from services.questionnaire_service import get_progress_metadata
            response_data["questionnaire"] = get_progress_metadata(active_agent, g_state)
        return response_data

    res_dict = result if isinstance(result, dict) else {}
    ans_text = res_dict.get("answer")
    if not ans_text:
        responses = res_dict.get("responses")
        if isinstance(responses, list) and responses:
            ans_text = str(responses[-1])
        else:
            ans_text = "Here is your generated trip plan."

    source_match = re.search(r"\n?\[SOURCE:([^\]]+)\]\s*$", ans_text or "")
    answer_source = source_match.group(1).strip() if source_match else ""
    if source_match:
        ans_text = re.sub(r"\n?\[SOURCE:[^\]]+\]\s*$", "", ans_text or "").strip()

    final_routes = res_dict.get("routes", [])
    if answer_source == "RAG Knowledge Service":
        final_routes = ["rag_service"]

    response_data = {
        "status": "success",
        "answer": ans_text,
        "routes": final_routes,
        "trip": None,
        "nearbyResult": res_dict.get("nearbyResult"), #added new line 443 for nearbyagent
        "metadata": {
            "source": "rag_service" if answer_source == "RAG Knowledge Service" else "guided_flow",
            "generated_by": "supervisor",
            "cached": False,
            "chat_flow": {
                "intent": flow_plan.intent,
                "confidence": flow_plan.confidence,
                "entities": flow_plan.entities,
                "reason": flow_plan.reason,
                "answer_source": answer_source,
            },
            "generated_at": datetime.now().isoformat()
        }
    }
    g_state = get_guided_state()
    active_agent = g_state.get("active_agent")
    if active_agent and g_state.get("agent_flow_active") == "1":
        from services.questionnaire_service import get_progress_metadata
        response_data["questionnaire"] = get_progress_metadata(active_agent, g_state)
    print(
        "[LOG][CHAT_RESPONSE] "
        f"trip=no, routes={response_data.get('routes', [])}, answer_chars={len(response_data.get('answer') or '')}, "
        f"nearbyResult={'yes' if response_data.get('nearbyResult') else 'no'}"
    )
    return response_data

CHAT_PROGRESS_EVENTS = [
    {
        "stage": "understanding",
        "message": "Planning your trip",
        "detail": "Reading destination, dates, budget, and intent."
    },
    {
        "stage": "transport",
        "message": "Searching travel options",
        "detail": "Choosing itinerary, places, food, weather, transport, or calendar agents."
    },
    {
        "stage": "places",
        "message": "Discovering nearby attractions",
        "detail": "Looking for relevant stays, restaurants, attractions, routes, and saved context."
    },
    {
        "stage": "hotels",
        "message": "Finding the best hotels",
        "detail": "Checking stay options and saved trip context."
    },
    {
        "stage": "restaurants",
        "message": "Looking for great restaurants",
        "detail": "Matching local dining options to the request."
    },
    {
        "stage": "building",
        "message": "Almost ready",
        "detail": "Preparing the final chat answer and any trip card data."
    },
]

def stream_event(event_type: str, **payload) -> str:
    return json.dumps({"type": event_type, **payload}, default=str) + "\n"

async def chat_stream_response(req: ChatRequest):
    async def event_generator():
        try:
            flow_plan = analyze_chat_flow(req.question)
            progress_events = flow_plan.loader_stages or CHAT_PROGRESS_EVENTS
            for idx, event in enumerate(progress_events, start=1):
                yield stream_event(
                    "progress",
                    index=idx,
                    total=len(progress_events),
                    **event
                )
                await asyncio.sleep(0.35)

            result = await asyncio.to_thread(chat, req)
            yield stream_event("final", data=result)
        except Exception as exc:
            yield stream_event("error", message=str(exc))

    return StreamingResponse(
        event_generator(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    return await chat_stream_response(req)

class CrowdPredictionRequest(BaseModel):
    destination: str
    city: Optional[str] = "Madurai"
    date: Optional[str] = None
    time: Optional[str] = "10:00"
    category: Optional[str] = "temple"

@app.post("/predict-crowd")
async def predict_crowd_endpoint(req: CrowdPredictionRequest):
    try:
        from services.crowd_service import crowd_service
        res = crowd_service.predict_crowd(
            destination=req.destination,
            city=req.city or "Madurai",
            date_str=req.date,
            time_str=req.time or "10:00",
            category=req.category or "temple"
        )
        return {"status": "success", "prediction": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/flights/search")
async def search_flights(
    from_airport: str = Query(..., alias="from"),
    to_airport: str = Query(..., alias="to"),
    date: str = Query(...)
):
    import base64
    import importlib.util
    import os
    
    # 1. Format date (must be YYYY-MM-DD)
    clean_date = date.strip()
    if len(clean_date) != 10 or "-" not in clean_date:
        from datetime import datetime, timedelta
        clean_date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        
    # 2. Build search URL (using the highly robust search query format)
    origin = from_airport.strip().upper()
    destination = to_airport.strip().upper()
    
    search_url = f"https://www.google.com/travel/flights/search?q=Flights%20from%20{origin}%20to%20{destination}%20on%20{clean_date}&curr=INR"

        
    print(f"Scraping Google Flights: {search_url}")
    
    # 3. Run scraper in a subprocess to avoid event loop conflicts in Uvicorn
    results = []
    try:
        scraper_dir = os.path.join(AI_ROOT, "google-flightpscraper.py")
        scraper_path = os.path.join(scraper_dir, "google-flights-scraper.py")
        
        if os.path.exists(scraper_path):
            import subprocess
            import uuid
            import tempfile
            
            # Save the temp JSON file in the OS temp directory so that Uvicorn's WatchFiles doesn't trigger a server reload
            temp_json_path = os.path.join(tempfile.gettempdir(), f"temp_flights_{uuid.uuid4().hex}.json")
            
            # Run the scraper as a subprocess using the current Python executable
            cmd = [sys.executable, scraper_path, search_url, temp_json_path]
            print(f"Executing flight scraper subprocess: {' '.join(cmd)}")
            
            # Run in a separate thread to not block the FastAPI event loop
            def run_proc():
                return subprocess.run(cmd, capture_output=True, text=True, timeout=90)
                
            proc_res = await asyncio.to_thread(run_proc)
            
            # Print stderr/stdout for backend logs/debugging
            if proc_res.stdout:
                print(f"Scraper stdout: {proc_res.stdout.strip()}")
            if proc_res.stderr:
                print(f"Scraper stderr: {proc_res.stderr.strip()}")
                
            # If the output file exists, read results
            if os.path.exists(temp_json_path):
                try:
                    with open(temp_json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        results = data.get("flights", [])
                finally:
                    # Cleanup the temp file
                    try:
                        os.remove(temp_json_path)
                    except Exception as clean_err:
                        print(f"Failed to remove temp file: {clean_err}")
            else:
                print(f"Warning: Scraper subprocess completed, but output file not found at: {temp_json_path}")
        else:
            print(f"Warning: Scraper file not found at: {scraper_path}")
    except Exception as scrap_err:
        print(f"Scraper error: {scrap_err}")
        
    # 4. Fallback to mock data if empty or error
    if not results:
        results = [
            {
                "airline": "Air India",
                "departure_time": "10:15 AM",
                "arrival_time": "12:30 PM",
                "duration": "2h 15m",
                "stops": "Nonstop",
                "price": "$120",
                "co2_emissions": "120 kg CO2",
                "emissions_variation": "-15% emissions"
            },
            {
                "airline": "IndiGo",
                "departure_time": "02:30 PM",
                "arrival_time": "04:45 PM",
                "duration": "2h 15m",
                "stops": "Nonstop",
                "price": "$98",
                "co2_emissions": "125 kg CO2",
                "emissions_variation": "-11% emissions"
            },
            {
                "airline": "Vistara",
                "departure_time": "06:00 PM",
                "arrival_time": "08:15 PM",
                "duration": "2h 15m",
                "stops": "Nonstop",
                "price": "$145",
                "co2_emissions": "118 kg CO2",
                "emissions_variation": "-16% emissions"
            }
        ]
        
    return {
        "success": True,
        "data": results
    }

@app.get("/api/buses/search")
async def search_buses(
    from_city: str = Query(..., alias="from"),
    to_city: str = Query(..., alias="to"),
    date: Optional[str] = None
):
    import base64
    import importlib.util
    import os
    import subprocess
    import uuid
    import tempfile
    from datetime import datetime, timedelta

    # 1. Format date (must be doj=DD-MMM-YYYY, e.g., 30-Jul-2026)
    clean_date = date.strip() if date else ""
    formatted_date = ""
    if clean_date and len(clean_date) == 10 and "-" in clean_date:
        try:
            parts = clean_date.split("-")
            year = parts[0]
            month_idx = int(parts[1]) - 1
            day = int(parts[2])
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            month_name = months[month_idx]
            formatted_date = f"{day}-{month_name}-{year}"
        except Exception as date_err:
            print(f"Error formatting redbus date: {date_err}")
            
    if not formatted_date:
        # Default to 15 days in advance
        d = datetime.now() + timedelta(days=15)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        formatted_date = f"{d.day}-{months[d.month - 1]}-{d.year}"

    # 2. Build search URL
    clean_from = from_city.lower().strip().replace(" ", "-")
    clean_to = to_city.lower().strip().replace(" ", "-")
    search_url = f"https://www.redbus.in/bus-tickets/{clean_from}-to-{clean_to}?doj={formatted_date}"
    print(f"Scraping redBus: {search_url}")

    # 3. Run scraper in a subprocess to avoid event loop conflicts in Uvicorn
    results = []
    try:
        scraper_dir = os.path.join(AI_ROOT, "redbus-scraper.py")
        scraper_path = os.path.join(scraper_dir, "redbus-scraper.py")
        
        if os.path.exists(scraper_path):
            # Save the temp JSON file in the OS temp directory
            temp_json_path = os.path.join(tempfile.gettempdir(), f"temp_buses_{uuid.uuid4().hex}.json")
            
            # Run the scraper as a subprocess using the current Python executable
            cmd = [sys.executable, scraper_path, search_url, temp_json_path]
            print(f"Executing bus scraper subprocess: {' '.join(cmd)}")
            
            # Run in a separate thread to not block the FastAPI event loop
            def run_proc():
                return subprocess.run(cmd, capture_output=True, text=True, timeout=90)
                
            proc_res = await asyncio.to_thread(run_proc)
            
            # Print stderr/stdout for backend logs/debugging
            if proc_res.stdout:
                print(f"Bus Scraper stdout: {proc_res.stdout.strip()}")
            if proc_res.stderr:
                print(f"Bus Scraper stderr: {proc_res.stderr.strip()}")
                
            # If the output file exists, read results
            if os.path.exists(temp_json_path):
                try:
                    with open(temp_json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        results = data.get("buses", [])
                finally:
                    # Cleanup the temp file
                    try:
                        os.remove(temp_json_path)
                    except Exception as clean_err:
                        print(f"Failed to remove temp file: {clean_err}")
            else:
                print(f"Warning: Bus scraper subprocess completed, but output file not found at: {temp_json_path}")
        else:
            print(f"Warning: Bus scraper file not found at: {scraper_path}")
    except Exception as scrap_err:
        print(f"Bus scraper error: {scrap_err}")

    # 4. Fallback to mock data if empty or error
    if not results:
        results = [
            {
                "operator": "SRS Travels",
                "type": "A/C Sleeper (2+1)",
                "departure_time": "21:00",
                "arrival_time": "05:30",
                "duration": "8h 30m",
                "price": "₹950",
                "rating": "4.2"
            },
            {
                "operator": "Parveen Travels",
                "type": "Volvo Multi-Axle I-Shift A/C Semi Sleeper (2+2)",
                "departure_time": "22:15",
                "arrival_time": "06:15",
                "duration": "8h 00m",
                "price": "₹1,150",
                "rating": "4.5"
            },
            {
                "operator": "IntrCity SmartBus",
                "type": "A/C Sleeper (2+1) - SmartBus",
                "departure_time": "21:30",
                "arrival_time": "05:50",
                "duration": "8h 20m",
                "price": "₹1,200",
                "rating": "4.6"
            },
            {
                "operator": "KPN Travels",
                "type": "Non A/C Sleeper (2+1)",
                "departure_time": "20:45",
                "arrival_time": "05:45",
                "duration": "9h 00m",
                "price": "₹750",
                "rating": "3.8"
            }
        ]
        
    return {
        "success": True,
        "data": results
    }


# -------------------------------------------------------------
# RailRadar APIs (to support the frontend search interface)
# -------------------------------------------------------------

@app.get("/api/stations/search")
def search_stations(q: str):
    results = []
    # Local lookup list of common stations
    common_stations = [
        {"code": "MAS", "name": "CHENNAI CENTRAL"},
        {"code": "MS", "name": "CHENNAI EGMORE"},
        {"code": "MDU", "name": "MADURAI JN"},
        {"code": "CBE", "name": "COIMBATORE JN"},
        {"code": "SBC", "name": "KSR BENGALURU"},
        {"code": "NDLS", "name": "NEW DELHI"},
        {"code": "NZM", "name": "HAZRAT NIZAMUDDIN"},
        {"code": "HWH", "name": "HOWRAH JN"},
        {"code": "SA", "name": "SALEM JN"},
        {"code": "TPJ", "name": "TIRUCHIRAPPALLI JN"},
        {"code": "TEN", "name": "TIRUNELVELI JN"},
        {"code": "CAPE", "name": "KANYAKUMARI"},
        {"code": "PDY", "name": "PUDUCHERRY"},
        {"code": "TJ", "name": "THANJAVUR JN"},
        {"code": "MV", "name": "MAYILADUTURAI JN"},
    ]
    query_lower = q.lower().strip()
    
    # Try calling the online station finder API via transport_agent key
    rapid_key = os.getenv("RAILRADAR_API_KEY")
    if rapid_key:
        try:
            import requests
            # Lookup via railradar lookup or findstations
            url = "https://irctc1.p.rapidapi.com/findstations.php"
            headers = {
                "x-rapidapi-host": "indianrailways.p.rapidapi.com",
                "x-rapidapi-key": rapid_key
            }
            params = {"station": q}
            res = requests.get(url, headers=headers, params=params, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if "Station" in data and isinstance(data["Station"], list):
                    for s in data["Station"]:
                        code = s.get("StationCode")
                        name = s.get("StationName", "")
                        if code:
                            results.append({"code": code.upper(), "name": name.title()})
        except Exception as e:
            print(f"Error in backend station search api: {e}")
            
    # Merge with local match if empty or to augment
    local_matches = [
        s for s in common_stations 
        if query_lower in s["code"].lower() or query_lower in s["name"].lower()
    ]
    for s in local_matches:
        if not any(r["code"] == s["code"] for r in results):
            results.append(s)
            
    return {
        "success": True,
        "data": results[:10]
    }

def map_railradar_train_to_frontend(t):
    # Resolve inner train info
    train_info = t.get("train") or {}
    if not isinstance(train_info, dict):
        train_info = {}

    # Resolve train number
    number = train_info.get("number") or train_info.get("train_number") or t.get("train_number") or t.get("number") or ""
    # Resolve train name
    name = train_info.get("name") or train_info.get("train_name") or t.get("train_name") or t.get("name") or "Unknown Train"
    # Resolve type
    train_type = train_info.get("type") or train_info.get("train_type") or t.get("train_type") or t.get("type") or "Express"
    
    # Resolve run days
    raw_days = train_info.get("runDays") or train_info.get("run_days") or t.get("runDays") or t.get("run_days") or t.get("days") or []
    run_days = []
    if isinstance(raw_days, list):
        run_days = [str(d).lower()[:3] for d in raw_days]
    elif isinstance(raw_days, str):
        run_days = [d.strip().lower()[:3] for d in raw_days.split(",")]
    if not run_days:
        run_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        
    # Resolve from departure
    from_data = t.get("from") or {}
    departure = ""
    if isinstance(from_data, dict):
        departure = from_data.get("departure") or from_data.get("time") or t.get("from_std") or t.get("departure") or "09:00"
    else:
        departure = t.get("from_std") or t.get("departure") or "09:00"
        
    # Resolve to arrival
    to_data = t.get("to") or {}
    arrival = ""
    if isinstance(to_data, dict):
        arrival = to_data.get("arrival") or to_data.get("time") or t.get("to_std") or t.get("arrival") or "17:00"
    else:
        arrival = t.get("to_std") or t.get("arrival") or "17:00"
        
    # Resolve distance
    distance = t.get("distance") or 0
    try:
        distance = int(distance)
    except:
        distance = 0
        
    # Resolve duration
    duration = t.get("duration") or 0
    duration_mins = 480
    if isinstance(duration, (int, float)):
        duration_mins = int(duration)
    elif isinstance(duration, str):
        if ":" in duration:
            parts = duration.split(":")
            try:
                duration_mins = int(parts[0]) * 60 + int(parts[1])
            except:
                pass
        elif "h" in duration or "m" in duration:
            h = 0
            m = 0
            import re
            h_match = re.search(r'(\d+)\s*h', duration)
            m_match = re.search(r'(\d+)\s*m', duration)
            if h_match:
                h = int(h_match.group(1))
            if m_match:
                m = int(m_match.group(1))
            duration_mins = h * 60 + m
    
    # Resolve halts
    halts = t.get("totalHaltsBetween") or t.get("halt_stations") or t.get("halts") or 0
    try:
        halts = int(halts)
    except:
        halts = 0
        
    return {
        "train": {
            "number": str(number),
            "name": name,
            "type": train_type,
            "runDays": run_days
        },
        "from": {
            "departure": departure,
            "arrival": None,
            "day": 1,
            "sequence": 1
        },
        "to": {
            "departure": None,
            "arrival": arrival,
            "day": 1,
            "sequence": 10
        },
        "distance": distance,
        "duration": duration_mins,
        "totalHaltsBetween": halts
    }
@app.get("/api/trains/between")
async def trains_between(
    from_code: str = Query(..., alias="from"),
    to_code: str = Query(..., alias="to"),
    date: Optional[str] = None,
    live: Optional[bool] = None
):
    from datetime import datetime, timedelta
    import os
    import subprocess
    import uuid
    import tempfile
    import json
    
    if not date or date == "undefined" or date == "None":
        date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        
    # Format date to DD-MM-YYYY for ConfirmTkt (e.g. 30-07-2026)
    formatted_date = ""
    try:
        if "-" in date:
            parts = date.split("-")
            if len(parts) == 3:
                if len(parts[0]) == 4: # YYYY-MM-DD
                    formatted_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                else: # DD-MM-YYYY or other
                    formatted_date = date
    except Exception as date_err:
        print(f"Error formatting train date: {date_err}")
        
    if not formatted_date:
        # Default to 15 days in advance
        d = datetime.now() + timedelta(days=15)
        formatted_date = f"{d.strftime('%d-%m-%Y')}"

    # Build search URL
    origin = from_code.strip().upper()
    destination = to_code.strip().upper()
    search_url = f"https://www.confirmtkt.com/rbooking/trains/from/{origin}/to/{destination}/{formatted_date}"
    print(f"Scraping ConfirmTkt: {search_url}")

    # Run scraper in a subprocess
    trains_list = []
    try:
        scraper_path = os.path.join(AI_ROOT, "train_scraper.py")
        if os.path.exists(scraper_path):
            temp_json_path = os.path.join(tempfile.gettempdir(), f"temp_trains_{uuid.uuid4().hex}.json")
            
            cmd = [sys.executable, scraper_path, search_url, temp_json_path]
            print(f"Executing train scraper subprocess: {' '.join(cmd)}")
            
            def run_proc():
                return subprocess.run(cmd, capture_output=True, text=True, timeout=90)
                
            proc_res = await asyncio.to_thread(run_proc)
            
            if proc_res.stdout:
                print(f"Train Scraper stdout: {proc_res.stdout.strip()}")
            if proc_res.stderr:
                print(f"Train Scraper stderr: {proc_res.stderr.strip()}")
                
            if os.path.exists(temp_json_path):
                try:
                    with open(temp_json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        trains_list = data.get("trains", [])
                finally:
                    try:
                        os.remove(temp_json_path)
                    except Exception as clean_err:
                        print(f"Failed to remove temp file: {clean_err}")
            else:
                print(f"Warning: Train scraper completed but output file not found at: {temp_json_path}")
        else:
            print(f"Warning: Train scraper file not found at: {scraper_path}")
    except Exception as scrap_err:
        print(f"Train scraper error: {scrap_err}")

    # Fallback to dummy data if API/scraper failed or returned nothing
    if not trains_list:
        trains_list = [
            {
                "train": {
                    "number": "12633",
                    "name": "Kanyakumari Express",
                    "type": "Superfast",
                    "runDays": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
                },
                "from": {
                    "departure": "17:20",
                    "arrival": None,
                    "day": 1,
                    "sequence": 1
                },
                "to": {
                    "departure": None,
                    "arrival": "01:20",
                    "day": 2,
                    "sequence": 15
                },
                "distance": 490,
                "duration": 480,
                "totalHaltsBetween": 8
            },
            {
                "train": {
                    "number": "12637",
                    "name": "Pandian Express",
                    "type": "Superfast",
                    "runDays": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
                },
                "from": {
                    "departure": "21:40",
                    "arrival": None,
                    "day": 1,
                    "sequence": 1
                },
                "to": {
                    "departure": None,
                    "arrival": "05:35",
                    "day": 2,
                    "sequence": 10
                },
                "distance": 495,
                "duration": 475,
                "totalHaltsBetween": 6
            }
        ]
            
    return {
        "success": True,
        "data": {
            "from": {"code": from_code.upper(), "name": from_code.upper() + " JN"},
            "to": {"code": to_code.upper(), "name": to_code.upper() + " JN"},
            "count": len(trains_list),
            "trains": trains_list
        }
    }


@app.get("/legacy/api/flights/search")
async def search_flights(
    from_airport: str = Query(..., alias="from"),
    to_airport: str = Query(..., alias="to"),
    date: str = Query(...)
):
    import base64
    import importlib.util
    import os
    
    # 1. Format date (must be YYYY-MM-DD)
    clean_date = date.strip()
    if len(clean_date) != 10 or "-" not in clean_date:
        from datetime import datetime, timedelta
        clean_date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        
    # 2. Build search URL (using the highly robust search query format)
    origin = from_airport.strip().upper()
    destination = to_airport.strip().upper()
    
    search_url = f"https://www.google.com/travel/flights/search?q=Flights%20from%20{origin}%20to%20{destination}%20on%20{clean_date}&curr=INR"

        
    print(f"Scraping Google Flights: {search_url}")
    
    # 3. Run scraper in a subprocess to avoid event loop conflicts in Uvicorn
    results = []
    try:
        scraper_dir = os.path.join(AI_ROOT, "google-flightpscraper.py")
        scraper_path = os.path.join(scraper_dir, "google-flights-scraper.py")
        
        if os.path.exists(scraper_path):
            import subprocess
            import uuid
            import tempfile
            
            # Save the temp JSON file in the OS temp directory so that Uvicorn's WatchFiles doesn't trigger a server reload
            temp_json_path = os.path.join(tempfile.gettempdir(), f"temp_flights_{uuid.uuid4().hex}.json")
            
            # Run the scraper as a subprocess using the current Python executable
            cmd = [sys.executable, scraper_path, search_url, temp_json_path]
            print(f"Executing flight scraper subprocess: {' '.join(cmd)}")
            
            # Run in a separate thread to not block the FastAPI event loop
            def run_proc():
                return subprocess.run(cmd, capture_output=True, text=True, timeout=90)
                
            proc_res = await asyncio.to_thread(run_proc)
            
            # Print stderr/stdout for backend logs/debugging
            if proc_res.stdout:
                print(f"Scraper stdout: {proc_res.stdout.strip()}")
            if proc_res.stderr:
                print(f"Scraper stderr: {proc_res.stderr.strip()}")
                
            # If the output file exists, read results
            if os.path.exists(temp_json_path):
                try:
                    with open(temp_json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        results = data.get("flights", [])
                finally:
                    # Cleanup the temp file
                    try:
                        os.remove(temp_json_path)
                    except Exception as clean_err:
                        print(f"Failed to remove temp file: {clean_err}")
            else:
                print(f"Warning: Scraper subprocess completed, but output file not found at: {temp_json_path}")
        else:
            print(f"Warning: Scraper file not found at: {scraper_path}")
    except Exception as scrap_err:
        print(f"Scraper error: {scrap_err}")
        
    # 4. Fallback to mock data if empty or error
    if not results:
        results = [
            {
                "airline": "Air India",
                "departure_time": "10:15 AM",
                "arrival_time": "12:30 PM",
                "duration": "2h 15m",
                "stops": "Nonstop",
                "price": "$120",
                "co2_emissions": "120 kg CO2",
                "emissions_variation": "-15% emissions"
            },
            {
                "airline": "IndiGo",
                "departure_time": "02:30 PM",
                "arrival_time": "04:45 PM",
                "duration": "2h 15m",
                "stops": "Nonstop",
                "price": "$98",
                "co2_emissions": "125 kg CO2",
                "emissions_variation": "-11% emissions"
            },
            {
                "airline": "Vistara",
                "departure_time": "06:00 PM",
                "arrival_time": "08:15 PM",
                "duration": "2h 15m",
                "stops": "Nonstop",
                "price": "$145",
                "co2_emissions": "118 kg CO2",
                "emissions_variation": "-16% emissions"
            }
        ]
        
    return {
        "success": True,
        "data": results
    }

@app.get("/api/buses/search")
async def search_buses(
    from_city: str = Query(..., alias="from"),
    to_city: str = Query(..., alias="to"),
    date: Optional[str] = None
):
    import base64
    import importlib.util
    import os
    import subprocess
    import uuid
    import tempfile
    from datetime import datetime, timedelta

    # 1. Format date (must be doj=DD-MMM-YYYY, e.g., 30-Jul-2026)
    clean_date = date.strip() if date else ""
    formatted_date = ""
    if clean_date and len(clean_date) == 10 and "-" in clean_date:
        try:
            parts = clean_date.split("-")
            year = parts[0]
            month_idx = int(parts[1]) - 1
            day = int(parts[2])
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            month_name = months[month_idx]
            formatted_date = f"{day}-{month_name}-{year}"
        except Exception as date_err:
            print(f"Error formatting redbus date: {date_err}")
            
    if not formatted_date:
        # Default to 15 days in advance
        d = datetime.now() + timedelta(days=15)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        formatted_date = f"{d.day}-{months[d.month - 1]}-{d.year}"

    # 2. Build search URL
    clean_from = from_city.lower().strip().replace(" ", "-")
    clean_to = to_city.lower().strip().replace(" ", "-")
    search_url = f"https://www.redbus.in/bus-tickets/{clean_from}-to-{clean_to}?doj={formatted_date}"
    print(f"Scraping redBus: {search_url}")

    # 3. Run scraper in a subprocess to avoid event loop conflicts in Uvicorn
    results = []
    try:
        scraper_dir = os.path.join(AI_ROOT, "redbus-scraper.py")
        scraper_path = os.path.join(scraper_dir, "redbus-scraper.py")
        
        if os.path.exists(scraper_path):
            # Save the temp JSON file in the OS temp directory
            temp_json_path = os.path.join(tempfile.gettempdir(), f"temp_buses_{uuid.uuid4().hex}.json")
            
            # Run the scraper as a subprocess using the current Python executable
            cmd = [sys.executable, scraper_path, search_url, temp_json_path]
            print(f"Executing bus scraper subprocess: {' '.join(cmd)}")
            
            # Run in a separate thread to not block the FastAPI event loop
            def run_proc():
                return subprocess.run(cmd, capture_output=True, text=True, timeout=90)
                
            proc_res = await asyncio.to_thread(run_proc)
            
            # Print stderr/stdout for backend logs/debugging
            if proc_res.stdout:
                print(f"Bus Scraper stdout: {proc_res.stdout.strip()}")
            if proc_res.stderr:
                print(f"Bus Scraper stderr: {proc_res.stderr.strip()}")
                
            # If the output file exists, read results
            if os.path.exists(temp_json_path):
                try:
                    with open(temp_json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        results = data.get("buses", [])
                finally:
                    # Cleanup the temp file
                    try:
                        os.remove(temp_json_path)
                    except Exception as clean_err:
                        print(f"Failed to remove temp file: {clean_err}")
            else:
                print(f"Warning: Bus scraper subprocess completed, but output file not found at: {temp_json_path}")
        else:
            print(f"Warning: Bus scraper file not found at: {scraper_path}")
    except Exception as scrap_err:
        print(f"Bus scraper error: {scrap_err}")

    # 4. Fallback to mock data if empty or error
    if not results:
        results = [
            {
                "operator": "SRS Travels",
                "type": "A/C Sleeper (2+1)",
                "departure_time": "21:00",
                "arrival_time": "05:30",
                "duration": "8h 30m",
                "price": "₹950",
                "rating": "4.2"
            },
            {
                "operator": "Parveen Travels",
                "type": "Volvo Multi-Axle I-Shift A/C Semi Sleeper (2+2)",
                "departure_time": "22:15",
                "arrival_time": "06:15",
                "duration": "8h 00m",
                "price": "₹1,150",
                "rating": "4.5"
            },
            {
                "operator": "IntrCity SmartBus",
                "type": "A/C Sleeper (2+1) - SmartBus",
                "departure_time": "21:30",
                "arrival_time": "05:50",
                "duration": "8h 20m",
                "price": "₹1,200",
                "rating": "4.6"
            },
            {
                "operator": "KPN Travels",
                "type": "Non A/C Sleeper (2+1)",
                "departure_time": "20:45",
                "arrival_time": "05:45",
                "duration": "9h 00m",
                "price": "₹750",
                "rating": "3.8"
            }
        ]
        
    return {
        "success": True,
        "data": results
    }


# -------------------------------------------------------------
# RailRadar APIs (to support the frontend search interface)
# -------------------------------------------------------------

@app.get("/api/stations/search")
def search_stations(q: str):
    results = []
    # Local lookup list of common stations
    common_stations = [
        {"code": "MAS", "name": "CHENNAI CENTRAL"},
        {"code": "MS", "name": "CHENNAI EGMORE"},
        {"code": "MDU", "name": "MADURAI JN"},
        {"code": "CBE", "name": "COIMBATORE JN"},
        {"code": "SBC", "name": "KSR BENGALURU"},
        {"code": "NDLS", "name": "NEW DELHI"},
        {"code": "NZM", "name": "HAZRAT NIZAMUDDIN"},
        {"code": "HWH", "name": "HOWRAH JN"},
        {"code": "SA", "name": "SALEM JN"},
        {"code": "TPJ", "name": "TIRUCHIRAPPALLI JN"},
        {"code": "TEN", "name": "TIRUNELVELI JN"},
        {"code": "CAPE", "name": "KANYAKUMARI"},
        {"code": "PDY", "name": "PUDUCHERRY"},
        {"code": "TJ", "name": "THANJAVUR JN"},
        {"code": "MV", "name": "MAYILADUTURAI JN"},
    ]
    query_lower = q.lower().strip()
    
    # Try calling the online station finder API via transport_agent key
    rapid_key = os.getenv("RAILRADAR_API_KEY")
    if rapid_key:
        try:
            import requests
            # Lookup via railradar lookup or findstations
            url = "https://irctc1.p.rapidapi.com/findstations.php"
            headers = {
                "x-rapidapi-host": "indianrailways.p.rapidapi.com",
                "x-rapidapi-key": rapid_key
            }
            params = {"station": q}
            res = requests.get(url, headers=headers, params=params, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if "Station" in data and isinstance(data["Station"], list):
                    for s in data["Station"]:
                        code = s.get("StationCode")
                        name = s.get("StationName", "")
                        if code:
                            results.append({"code": code.upper(), "name": name.title()})
        except Exception as e:
            print(f"Error in backend station search api: {e}")
            
    # Merge with local match if empty or to augment
    local_matches = [
        s for s in common_stations 
        if query_lower in s["code"].lower() or query_lower in s["name"].lower()
    ]
    for s in local_matches:
        if not any(r["code"] == s["code"] for r in results):
            results.append(s)
            
    return {
        "success": True,
        "data": results[:10]
    }

def map_railradar_train_to_frontend(t):
    # Resolve inner train info
    train_info = t.get("train") or {}
    if not isinstance(train_info, dict):
        train_info = {}

    # Resolve train number
    number = train_info.get("number") or train_info.get("train_number") or t.get("train_number") or t.get("number") or ""
    # Resolve train name
    name = train_info.get("name") or train_info.get("train_name") or t.get("train_name") or t.get("name") or "Unknown Train"
    # Resolve type
    train_type = train_info.get("type") or train_info.get("train_type") or t.get("train_type") or t.get("type") or "Express"
    
    # Resolve run days
    raw_days = train_info.get("runDays") or train_info.get("run_days") or t.get("runDays") or t.get("run_days") or t.get("days") or []
    run_days = []
    if isinstance(raw_days, list):
        run_days = [str(d).lower()[:3] for d in raw_days]
    elif isinstance(raw_days, str):
        run_days = [d.strip().lower()[:3] for d in raw_days.split(",")]
    if not run_days:
        run_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        
    # Resolve from departure
    from_data = t.get("from") or {}
    departure = ""
    if isinstance(from_data, dict):
        departure = from_data.get("departure") or from_data.get("time") or t.get("from_std") or t.get("departure") or "09:00"
    else:
        departure = t.get("from_std") or t.get("departure") or "09:00"
        
    # Resolve to arrival
    to_data = t.get("to") or {}
    arrival = ""
    if isinstance(to_data, dict):
        arrival = to_data.get("arrival") or to_data.get("time") or t.get("to_std") or t.get("arrival") or "17:00"
    else:
        arrival = t.get("to_std") or t.get("arrival") or "17:00"
        
    # Resolve distance
    distance = t.get("distance") or 0
    try:
        distance = int(distance)
    except:
        distance = 0
        
    # Resolve duration
    duration = t.get("duration") or 0
    duration_mins = 480
    if isinstance(duration, (int, float)):
        duration_mins = int(duration)
    elif isinstance(duration, str):
        if ":" in duration:
            parts = duration.split(":")
            try:
                duration_mins = int(parts[0]) * 60 + int(parts[1])
            except:
                pass
        elif "h" in duration or "m" in duration:
            h = 0
            m = 0
            import re
            h_match = re.search(r'(\d+)\s*h', duration)
            m_match = re.search(r'(\d+)\s*m', duration)
            if h_match:
                h = int(h_match.group(1))
            if m_match:
                m = int(m_match.group(1))
            duration_mins = h * 60 + m
    
    # Resolve halts
    halts = t.get("totalHaltsBetween") or t.get("halt_stations") or t.get("halts") or 0
    try:
        halts = int(halts)
    except:
        halts = 0
        
    return {
        "train": {
            "number": str(number),
            "name": name,
            "type": train_type,
            "runDays": run_days
        },
        "from": {
            "departure": departure,
            "arrival": None,
            "day": 1,
            "sequence": 1
        },
        "to": {
            "departure": None,
            "arrival": arrival,
            "day": 1,
            "sequence": 10
        },
        "distance": distance,
        "duration": duration_mins,
        "totalHaltsBetween": halts
    }
@app.get("/api/trains/between")
async def trains_between(
    from_code: str = Query(..., alias="from"),
    to_code: str = Query(..., alias="to"),
    date: Optional[str] = None,
    live: Optional[bool] = None
):
    from datetime import datetime, timedelta
    import os
    import subprocess
    import uuid
    import tempfile
    import json
    
    if not date or date == "undefined" or date == "None":
        date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        
    # Format date to DD-MM-YYYY for ConfirmTkt (e.g. 30-07-2026)
    formatted_date = ""
    try:
        if "-" in date:
            parts = date.split("-")
            if len(parts) == 3:
                if len(parts[0]) == 4: # YYYY-MM-DD
                    formatted_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                else: # DD-MM-YYYY or other
                    formatted_date = date
    except Exception as date_err:
        print(f"Error formatting train date: {date_err}")
        
    if not formatted_date:
        # Default to 15 days in advance
        d = datetime.now() + timedelta(days=15)
        formatted_date = f"{d.strftime('%d-%m-%Y')}"

    # Build search URL
    origin = from_code.strip().upper()
    destination = to_code.strip().upper()
    search_url = f"https://www.confirmtkt.com/rbooking/trains/from/{origin}/to/{destination}/{formatted_date}"
    print(f"Scraping ConfirmTkt: {search_url}")

    # Run scraper in a subprocess
    trains_list = []
    try:
        scraper_path = os.path.join(AI_ROOT, "train_scraper.py")
        if os.path.exists(scraper_path):
            temp_json_path = os.path.join(tempfile.gettempdir(), f"temp_trains_{uuid.uuid4().hex}.json")
            
            cmd = [sys.executable, scraper_path, search_url, temp_json_path]
            print(f"Executing train scraper subprocess: {' '.join(cmd)}")
            
            def run_proc():
                return subprocess.run(cmd, capture_output=True, text=True, timeout=90)
                
            proc_res = await asyncio.to_thread(run_proc)
            
            if proc_res.stdout:
                print(f"Train Scraper stdout: {proc_res.stdout.strip()}")
            if proc_res.stderr:
                print(f"Train Scraper stderr: {proc_res.stderr.strip()}")
                
            if os.path.exists(temp_json_path):
                try:
                    with open(temp_json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        trains_list = data.get("trains", [])
                finally:
                    try:
                        os.remove(temp_json_path)
                    except Exception as clean_err:
                        print(f"Failed to remove temp file: {clean_err}")
            else:
                print(f"Warning: Train scraper completed but output file not found at: {temp_json_path}")
        else:
            print(f"Warning: Train scraper file not found at: {scraper_path}")
    except Exception as scrap_err:
        print(f"Train scraper error: {scrap_err}")

    # Fallback to dummy data if API/scraper failed or returned nothing
    if not trains_list:
        trains_list = [
            {
                "train": {
                    "number": "12633",
                    "name": "Kanyakumari Express",
                    "type": "Superfast",
                    "runDays": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
                },
                "from": {
                    "departure": "17:20",
                    "arrival": None,
                    "day": 1,
                    "sequence": 1
                },
                "to": {
                    "departure": None,
                    "arrival": "01:20",
                    "day": 2,
                    "sequence": 15
                },
                "distance": 490,
                "duration": 480,
                "totalHaltsBetween": 8
            },
            {
                "train": {
                    "number": "12637",
                    "name": "Pandian Express",
                    "type": "Superfast",
                    "runDays": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
                },
                "from": {
                    "departure": "21:40",
                    "arrival": None,
                    "day": 1,
                    "sequence": 1
                },
                "to": {
                    "departure": None,
                    "arrival": "05:35",
                    "day": 2,
                    "sequence": 10
                },
                "distance": 495,
                "duration": 475,
                "totalHaltsBetween": 6
            }
        ]
            
    return {
        "success": True,
        "data": {
            "from": {"code": from_code.upper(), "name": from_code.upper() + " JN"},
            "to": {"code": to_code.upper(), "name": to_code.upper() + " JN"},
            "count": len(trains_list),
            "trains": trains_list
        }
    }


@app.get("/legacy/api/trains/between")
async def trains_between(
    from_code: str = Query(..., alias="from"),
    to_code: str = Query(..., alias="to"),
    date: Optional[str] = None,
    live: Optional[bool] = None
):
    return await travel_trains_between(from_code=from_code, to_code=to_code, date=date, live=live)


class OptimizeRoutePlace(BaseModel):
    name: str

class OptimizeRouteRequest(BaseModel):
    cityName: str
    hotelName: str
    hotelLat: float
    hotelLng: float
    places: List[OptimizeRoutePlace]
    startLocation: Optional[str] = None

@app.post("/optimize-route")
def optimize_route_endpoint(req: OptimizeRouteRequest):
    return travel_optimize_route_endpoint(req)


@app.post("/api/budget/calculate")
def calculate_budget(req: dict):
    return travel_calculate_budget(req)


@app.get("/api/exchange-rates")
def get_exchange_rates():
    return travel_get_exchange_rates()


@app.post("/calendar/save")
def save_calendar(req: SaveCalendarRequest):
    return calendar_save(req)

@app.post("/calendar/save-and-sync")
def save_and_sync(req: SaveAndSyncRequest):
    return calendar_save_and_sync(req)

@app.get("/calendar/export")
def export_calendar(trip_name: str):
    return calendar_export(trip_name)

@app.get("/trips/{trip_id}")
def get_trip_by_id(trip_id: str):
    return calendar_get_trip_by_id(trip_id)

@app.get("/login/google")
def login_google(trip_id: str):
    return calendar_login_google(trip_id)

@app.get("/oauth2callback")
def oauth2callback(code: str, state: str):
    return calendar_oauth2callback(code=code, state=state)
    
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
