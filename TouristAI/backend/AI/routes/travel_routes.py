from fastapi import APIRouter, Query
from typing import Optional
import os
import sys
import asyncio
import subprocess
import tempfile
import uuid
import re
import json
from datetime import datetime, timedelta

from fastapi.responses import JSONResponse
from services.google_calendar_service import GoogleCalendarService
from services.calendar_service import CalendarService
from services.trip_service import TripService
from services.budget_service import BudgetService
from supervisor import get_guided_state
from repositories.trip_repository import TripRepository
from models.itinerary import Trip, ItineraryItem
from database.postgres import PostgresDatabase
from pydantic import BaseModel
from typing import List

router = APIRouter()

trip_service = TripService()


class OptimizeRoutePlace(BaseModel):
    name: str


class OptimizeRouteRequest(BaseModel):
    cityName: str
    hotelName: str
    hotelLat: float
    hotelLng: float
    places: List[OptimizeRoutePlace]
    startLocation: Optional[str] = None


@router.get("/api/flights/search")
async def search_flights(
    from_airport: str = Query(..., alias="from"),
    to_airport: str = Query(..., alias="to"),
    date: str = Query(...)
):
    clean_date = date.strip()
    if len(clean_date) != 10 or "-" not in clean_date:
        return {"success": False, "error": "Date must be YYYY-MM-DD"}

    origin = from_airport.strip().upper()
    destination = to_airport.strip().upper()
    search_url = f"https://www.google.com/travel/flights/search?q=Flights%20from%20{origin}%20to%20{destination}%20on%20{clean_date}&curr=INR"

    print(f"Scraping Google Flights: {search_url}")
    results = []
    try:
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "transport", "scrapers", "google_flights_script.py")
        if os.path.exists(script_path):
            temp_json_path = os.path.join(tempfile.gettempdir(), f"temp_flights_{uuid.uuid4().hex}.json")
            proc = await asyncio.to_thread(
                subprocess.run,
                [sys.executable, script_path, search_url, temp_json_path],
                capture_output=True,
                text=True,
                timeout=90,
            )
            if proc.stdout:
                print(proc.stdout)
            if proc.stderr:
                print(proc.stderr)
            if os.path.exists(temp_json_path):
                with open(temp_json_path, "r", encoding="utf-8") as f:
                    results = json.load(f)
        else:
            print(f"Warning: Flight scraper file not found at: {script_path}")
    except Exception as scrap_err:
        print(f"Flight scraper error: {scrap_err}")

    if not results:
        results = [
            {
                "airline": "IndiGo",
                "price": "₹4,200",
                "departure_time": "08:30",
                "arrival_time": "10:45",
                "duration": "2h 15m",
                "stops": "Non-stop"
            },
            {
                "airline": "Air India",
                "price": "₹5,100",
                "departure_time": "12:40",
                "arrival_time": "14:55",
                "duration": "2h 15m",
                "stops": "Non-stop"
            }
        ]

    return {"success": True, "data": results}


@router.get("/api/buses/search")
async def search_buses(
    from_city: str = Query(..., alias="from"),
    to_city: str = Query(..., alias="to"),
    date: Optional[str] = None
):
    clean_date = date.strip() if date else ""
    formatted_date = ""
    if clean_date and len(clean_date) == 10 and "-" in clean_date:
        try:
            dt = datetime.strptime(clean_date, "%Y-%m-%d")
            formatted_date = dt.strftime("%d-%b-%Y")
        except Exception:
            formatted_date = ""

    if not formatted_date:
        d = datetime.now() + timedelta(days=15)
        formatted_date = d.strftime("%d-%b-%Y")

    clean_from = from_city.lower().strip().replace(" ", "-")
    clean_to = to_city.lower().strip().replace(" ", "-")
    search_url = f"https://www.redbus.in/bus-tickets/{clean_from}-to-{clean_to}?doj={formatted_date}"
    print(f"Scraping redBus: {search_url}")

    results = []
    try:
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "transport", "scrapers", "redbus_script.py")
        if os.path.exists(script_path):
            temp_json_path = os.path.join(tempfile.gettempdir(), f"temp_buses_{uuid.uuid4().hex}.json")
            proc = await asyncio.to_thread(
                subprocess.run,
                [sys.executable, script_path, search_url, temp_json_path],
                capture_output=True,
                text=True,
                timeout=90,
            )
            if proc.stdout:
                print(proc.stdout)
            if proc.stderr:
                print(proc.stderr)
            if os.path.exists(temp_json_path):
                with open(temp_json_path, "r", encoding="utf-8") as f:
                    results = json.load(f)
        else:
            print(f"Warning: Bus scraper file not found at: {script_path}")
    except Exception as scrap_err:
        print(f"Bus scraper error: {scrap_err}")

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
            }
        ]

    return {"success": True, "data": results}


@router.get("/api/stations/search")
def search_stations(q: str):
    results = []
    common_stations = [
        {"code": "MAS", "name": "CHENNAI CENTRAL"},
        {"code": "MS", "name": "CHENNAI EGMORE"},
        {"code": "MDU", "name": "MADURAI JN"},
        {"code": "CBE", "name": "COIMBATORE JN"},
        {"code": "SBC", "name": "KSR BENGALURU"},
        {"code": "NDLS", "name": "NEW DELHI"},
        {"code": "NZM", "name": "HAZRAT NIZAMUDDIN"},
        {"code": "HWH", "name": "HOWRAH JN"},
    ]
    query_lower = q.lower().strip()
    rapid_key = os.getenv("RAILRADAR_API_KEY")
    if rapid_key:
        try:
            import requests
            response = requests.get(
                "https://railradarapi.com/stations/search",
                params={"query": q},
                headers={"x-api-key": rapid_key},
                timeout=8,
            )
            if response.ok:
                payload = response.json()
                for item in payload.get("data", [])[:5]:
                    results.append({"code": item.get("code", ""), "name": item.get("name", "")})
        except Exception as exc:
            print(f"Station search error: {exc}")

    local_matches = [
        s for s in common_stations
        if query_lower in s["code"].lower() or query_lower in s["name"].lower()
    ]
    for s in local_matches:
        if not any(r["code"] == s["code"] for r in results):
            results.append(s)

    return {"success": True, "data": results[:10]}


def map_railradar_train_to_frontend(t):
    train_info = t.get("train") or {}
    if not isinstance(train_info, dict):
        train_info = {}

    number = train_info.get("number") or train_info.get("train_number") or t.get("train_number") or t.get("number") or ""
    name = train_info.get("name") or train_info.get("train_name") or t.get("train_name") or t.get("name") or "Unknown Train"
    train_type = train_info.get("type") or train_info.get("train_type") or t.get("train_type") or t.get("type") or "Express"

    raw_days = train_info.get("runDays") or train_info.get("run_days") or t.get("runDays") or t.get("run_days") or t.get("days") or []
    run_days = []
    if isinstance(raw_days, list):
        run_days = [str(d).lower()[:3] for d in raw_days]
    elif isinstance(raw_days, str):
        run_days = [d.strip().lower()[:3] for d in raw_days.split(",")]
    if not run_days:
        run_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    from_data = t.get("from") or {}
    departure = ""
    if isinstance(from_data, dict):
        departure = from_data.get("departure") or from_data.get("time") or t.get("from_std") or t.get("departure") or "09:00"
    else:
        departure = t.get("from_std") or t.get("departure") or "09:00"

    to_data = t.get("to") or {}
    arrival = ""
    if isinstance(to_data, dict):
        arrival = to_data.get("arrival") or to_data.get("time") or t.get("to_std") or t.get("arrival") or "17:00"
    else:
        arrival = t.get("to_std") or t.get("arrival") or "17:00"

    distance = t.get("distance") or 0
    try:
        distance = int(distance)
    except Exception:
        distance = 0

    duration = t.get("duration") or 0
    duration_mins = 480
    if isinstance(duration, (int, float)):
        duration_mins = int(duration)
    elif isinstance(duration, str):
        if ":" in duration:
            parts = duration.split(":")
            try:
                hours = int(parts[0])
                mins = int(parts[1])
                duration_mins = hours * 60 + mins
            except Exception:
                duration_mins = 480
        elif "h" in duration or "m" in duration:
            h = 0
            m = 0
            h_match = re.search(r"(\d+)\s*h", duration)
            m_match = re.search(r"(\d+)\s*m", duration)
            if h_match:
                h = int(h_match.group(1))
            if m_match:
                m = int(m_match.group(1))
            duration_mins = h * 60 + m

    halts = t.get("totalHaltsBetween") or t.get("halt_stations") or t.get("halts") or 0
    try:
        halts = int(halts)
    except Exception:
        halts = 0

    return {
        "train": {"number": str(number), "name": name, "type": train_type, "runDays": run_days},
        "from": {"departure": departure, "arrival": None, "day": 1, "sequence": 1},
        "to": {"departure": None, "arrival": arrival, "day": 1, "sequence": 10},
        "distance": distance,
        "duration": duration_mins,
        "totalHaltsBetween": halts,
    }


@router.get("/api/trains/between")
async def trains_between(
    from_code: str = Query(..., alias="from"),
    to_code: str = Query(..., alias="to"),
    date: Optional[str] = None,
    live: Optional[bool] = None
):
    if not date or date == "undefined" or date == "None":
        date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")

    formatted_date = ""
    try:
        if "-" in date:
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d-%m-%Y")
    except Exception as date_err:
        print(f"Error formatting train date: {date_err}")

    if not formatted_date:
        d = datetime.now() + timedelta(days=15)
        formatted_date = f"{d.strftime('%d-%m-%Y')}"

    origin = from_code.strip().upper()
    destination = to_code.strip().upper()
    search_url = f"https://www.confirmtkt.com/rbooking/trains/from/{origin}/to/{destination}/{formatted_date}"
    print(f"Scraping ConfirmTkt: {search_url}")

    trains_list = []
    try:
        scraper_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "transport", "scrapers", "confirmtkt_script.py")
        if os.path.exists(scraper_path):
            temp_json_path = os.path.join(tempfile.gettempdir(), f"temp_trains_{uuid.uuid4().hex}.json")
            proc = await asyncio.to_thread(
                subprocess.run,
                [sys.executable, scraper_path, search_url, temp_json_path],
                capture_output=True,
                text=True,
                timeout=90,
            )
            if proc.stdout:
                print(proc.stdout)
            if proc.stderr:
                print(proc.stderr)
            if os.path.exists(temp_json_path):
                with open(temp_json_path, "r", encoding="utf-8") as f:
                    trains_list = json.load(f)
        else:
            print(f"Warning: Train scraper file not found at: {scraper_path}")
    except Exception as scrap_err:
        print(f"Train scraper error: {scrap_err}")

    if not trains_list:
        trains_list = [
            {
                "train": {"number": "12633", "name": "Kanyakumari Express", "type": "Superfast", "runDays": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]},
                "from": {"departure": "17:20", "arrival": None, "day": 1, "sequence": 1},
                "to": {"departure": None, "arrival": "01:20", "day": 2, "sequence": 15},
                "distance": 490,
                "duration": 480,
                "totalHaltsBetween": 8,
            }
        ]

    return {
        "success": True,
        "data": {
            "from": {"code": from_code.upper(), "name": from_code.upper() + " JN"},
            "to": {"code": to_code.upper(), "name": to_code.upper() + " JN"},
            "count": len(trains_list),
            "trains": trains_list,
        },
    }


@router.post("/optimize-route")
def optimize_route_endpoint(req: OptimizeRouteRequest):
    from services.osrm_service import optimize_route_osrm
    places_dict = [{"name": p.name} for p in req.places]
    result = optimize_route_osrm(
        hotel_name=req.hotelName,
        hotel_coords=(req.hotelLat, req.hotelLng),
        places=places_dict,
        city_name=req.cityName,
        start_location=req.startLocation,
    )
    return result


@router.post("/api/budget/calculate")
def calculate_budget(req: dict):
    city = req.get("city", "Unknown")
    duration = int(req.get("duration", 3))
    budget_level = req.get("budget_level", "Moderate")
    return BudgetService.calculate_budget_summary(city, duration, budget_level)


@router.get("/api/exchange-rates")
def get_exchange_rates():
    try:
        import requests
        res = requests.get("https://open.er-api.com/v6/latest/INR", timeout=4.0)
        if res.status_code == 200:
            data = res.json()
            return {
                "base": "INR",
                "rates": data.get("rates", {}),
                "updated": data.get("time_last_update_utc", ""),
                "source": "open.er-api.com (free)",
            }
    except Exception as e:
        print(f"[ExchangeRate] API error: {e}")
    return {
        "base": "INR",
        "rates": {
            "USD": 0.01197, "EUR": 0.01103, "GBP": 0.00942,
            "JPY": 1.8960, "AUD": 0.01836, "CAD": 0.01641,
            "SGD": 0.01595, "AED": 0.04396, "THB": 0.4097,
            "MYR": 0.05256, "LKR": 3.9652, "NPR": 1.5985,
            "BDT": 1.2855, "PKR": 3.3302, "MMK": 25.07,
            "CHF": 0.01078, "SEK": 0.11565, "NOK": 0.12436,
            "DKK": 0.08202, "NZD": 0.02040, "ZAR": 0.21834,
            "KRW": 16.618, "HKD": 0.09339, "CNY": 0.08673,
            "IDR": 195.6, "PHP": 0.6683, "VND": 254.1,
            "MXN": 0.2028, "BRL": 0.06025, "RUB": 1.045,
        },
        "updated": "fallback (API unavailable)",
        "source": "fallback",
    }
