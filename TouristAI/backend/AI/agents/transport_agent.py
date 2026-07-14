import os
import json
import requests
from datetime import datetime
from rag_service import get_answer, save_to_rag, client
import re
import urllib.parse


RAILRADAR_API_KEY = os.getenv("RAILRADAR_API_KEY")
BASE_URL = "https://api.railradar.in"


# -----------------------------
# Flight Search
# -----------------------------
def get_flights(source, destination, date):
    # Placeholder. Replace with a real flight API if available.
    return None


# -----------------------------
# Get station code
# -----------------------------
def get_station_code(name):
    # Clean up the name: remove spaces, convert to uppercase
    cleaned_name = re.sub(r'\s+', '', name).upper()

    print(f"🔍 Looking up station code for: '{name}' (cleaned: '{cleaned_name}')")

    # If it's already a valid station code (2-4 uppercase letters), use it directly
    if len(cleaned_name) >= 2 and len(cleaned_name) <= 4 and cleaned_name.isalpha():
        print(f"🔍 '{name}' appears to be a station code, using '{cleaned_name}' directly")
        return cleaned_name

    # Common city name to station code mapping (fallback)
    city_to_code = {
        'CHENNAI': 'MAS',
        'MADRURAI': 'MDU',
        'MADURAI': 'MDU',
        'COIMBATORE': 'CBE',
        'BANGALORE': 'SBC',
        'BENGALURU': 'SBC',
        'DELHI': 'NDLS',
        'MUMBAI': 'BCT',
        'KOLKATA': 'HWH',
        'HYDERABAD': 'HYD',
        'SALEM': 'SA',
        'TRICHY': 'TPJ',
        'TIRUCHIRAPPALLI': 'TPJ',
        'TIRUNELVELI': 'TEN',
    }

    # Check if the cleaned name matches a known city
    if cleaned_name in city_to_code:
        code = city_to_code[cleaned_name]
        print(f"🔍 Found station code for '{cleaned_name}': {code}")
        return code

    # Try partial match
    for city, code in city_to_code.items():
        if cleaned_name in city or city in cleaned_name:
            print(f"🔍 Partial match: '{cleaned_name}' -> '{city}' -> {code}")
            return code

    # Otherwise, look it up via RailRadar's own station lookup endpoint
    result = query_railradar_api("v1/lookup/trains")  # placeholder if no dedicated station-search endpoint is wired up yet
    # NOTE: swap this for RailRadar's actual station-search endpoint (e.g. v1/stations/search?q=)
    # once you confirm the exact path in their docs — leaving lookup_trains() below as the
    # generic helper for now.
    print(f"⚠️ No local match for '{name}' and no RailRadar station-search endpoint wired up yet")
    return None


# -----------------------------
# Format date
# -----------------------------
def format_date(date_str):
    # Handle various date formats: DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD
    try:
        if "-" in date_str:
            parts = date_str.split("-")
            if len(parts[0]) == 4:  # YYYY-MM-DD
                return date_str  # Already in correct format
            elif len(parts[2]) == 4:  # DD-MM-YYYY
                return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
        elif "/" in date_str:
            return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        return date_str
    except Exception as e:
        print(f"⚠️ Date format error for '{date_str}': {e}")
        return date_str


# -----------------------------
# RailRadar API helper
# -----------------------------
session = requests.Session()

def query_railradar_api(endpoint: str, params: dict = None):
    """
    Generic helper to query api.railradar.in using RailRadar's Bearer auth.
    """
    url = f"{BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {RAILRADAR_API_KEY}",
        "Accept": "application/json",
    }
    try:
        print(f"🔍 Querying RailRadar API: {url} with params: {params}")
        r = session.get(url, headers=headers, params=params, timeout=15)
        print(f"🔍 RailRadar Response Status: {r.status_code}")

        if r.status_code == 200:
            try:
                return r.json()
            except Exception as decode_err:
                print(f"❌ JSON Decode Error on Status 200: {decode_err}")
                print(f"🔍 Raw response body: '{r.text[:1000]}'")
                return None
        else:
            print(f"⚠️ RailRadar API returned {r.status_code}: {r.text[:300]}")
    except Exception as e:
        print(f"❌ Exception querying RailRadar API: {e}")
    return None


# -----------------------------
# Train Search
# -----------------------------
def get_trains(source, destination, date):
    print(f"Searching trains from {source} to {destination} on {date}...")

    if not RAILRADAR_API_KEY:
        print("⚠️ Missing RAILRADAR_API_KEY")
        return None

    # Convert city names to station codes
    from_code = get_station_code(source)
    to_code = get_station_code(destination)

    if not from_code or not to_code:
        print(f"⚠️ Could not find station codes for '{source}' or '{destination}'")
        return None

    print(f"🔍 Station codes: {from_code} → {to_code}")

    # Format date to YYYY-MM-DD
    formatted_date = format_date(date)
    print(f"🔍 Formatted date: {formatted_date}")

    endpoint = f"v1/trains/between/{from_code}/{to_code}"
    params = {}
    if formatted_date:
        params["date"] = formatted_date

    return query_railradar_api(endpoint, params)



# -----------------------------
# Bus Search
# -----------------------------
def get_buses(source, destination, date):
    # Placeholder. Replace with a real bus API if available.
    return None


# -----------------------------
# Train booking links
# -----------------------------
def build_train_booking_links(source_name="", destination_name="", journey_date="", from_code="", to_code=""):
    links = {
        "irctc": "https://www.irctc.co.in/nget/train-search",
        "makemytrip": "https://www.makemytrip.com/railways/",
        "redbus": "https://www.redbus.in/",
    }

    if from_code and to_code and journey_date:
        links["irctc"] = (
            "https://www.irctc.co.in/nget/train-search"
            f"?fromStation={from_code}&toStation={to_code}&journeyDate={journey_date}"
        )

    if source_name and destination_name:
        query = urllib.parse.quote_plus(f"{source_name} to {destination_name} train")
        links["makemytrip"] = f"https://www.makemytrip.com/railways/?q={query}"
        links["redbus"] = f"https://www.redbus.in/search?from={urllib.parse.quote_plus(source_name)}&to={urllib.parse.quote_plus(destination_name)}"

    return links


# -----------------------------
# Format Response (RailRadar schema only)
# -----------------------------
def format_transport(flights, trains, buses, date="", source_name="", destination_name="", from_code="", to_code=""):
    output = []

    # RailRadar's "trains between stations" response shape:
    # { "success": true, "data": { "from": {...}, "to": {...}, "count": N, "trains": [ {...} ] } }
    train_list = None
    if isinstance(trains, dict):
        data = trains.get("data")
        if isinstance(data, dict):
            train_list = data.get("trains")

    if train_list:
        for idx, t in enumerate(train_list[:5], 1):
            train_info = t.get("train", {})
            train_name = train_info.get("name", "Unknown")
            train_number = train_info.get("number", "")
            train_type = train_info.get("type", "")
            run_days = train_info.get("runDays", [])

            departure = t.get("from", {}).get("departure", "")
            arrival = t.get("to", {}).get("arrival", "")
            duration_mins = t.get("duration", 0)
            distance = t.get("distance", 0)
            halts = t.get("totalHaltsBetween", 0)

            duration_str = f"{duration_mins // 60}h {duration_mins % 60}m" if duration_mins else ""

            output.append(f"{idx}. **{train_name} ({train_number})**")
            output.append(f"- 🚂 Type: {train_type}")
            output.append(f"- ⏰ Departure: {departure}")
            output.append(f"- ⏰ Arrival: {arrival}")
            output.append(f"- ⏱️ Duration: {duration_str}")
            output.append(f"- 📏 Distance: {distance} km")
            output.append(f"- 🛑 Halts: {halts}")
            if run_days:
                output.append(f"- 📅 Runs: {', '.join(run_days)}")

            booking_links = build_train_booking_links(
                source_name=source_name,
                destination_name=destination_name,
                journey_date=date,
                from_code=from_code,
                to_code=to_code,
            )
            output.append(
                f"🔎 Book now: [IRCTC]({booking_links['irctc']}) | "
                f"[MakeMyTrip]({booking_links['makemytrip']}) | "
                f"[RedBus]({booking_links['redbus']})"
            )
            output.append("")
    else:
        output.append("No Trains Found")

    return "\n".join(output)


# -----------------------------
# Main Agent
# -----------------------------
def transport_agent(question,
                    source="None",
                    destination="None",
                    date="None"):

    cache_key = f"{source}_{destination}_{date}"

    # 1. Check RAG
    try:
        rag = get_answer(cache_key, check_rag_only=True)
        if rag:
            print("✅ Found transport info in RAG cache.")
            return rag
    except Exception as e:
        print(f"⚠️ RAG check failed for transport: {e}")

    # 2. Search APIs
    print("ℹ️ No cache hit. Calling transport APIs.")
    trains = get_trains(source, destination, date)

    # If the API fails, use a final LLM fallback
    if not trains:
        print("⚠️ Transport API failed. Falling back to Groq LLM.")
        return get_answer(question)  # This will call Groq and save to RAG

    from_code = get_station_code(source)
    to_code = get_station_code(destination)

    answer = format_transport(
        None,
        trains,
        None,
        date=date,
        source_name=source,
        destination_name=destination,
        from_code=from_code,
        to_code=to_code,
    )

    # 3. Save
    try:
        save_to_rag(cache_key, answer)
        print("✅ Saved transport API response to RAG.")
    except Exception as e:
        print(f"⚠️ Could not save transport response to RAG: {e}")

    return {
        "source": "transport_api",
        "answer": answer
    }