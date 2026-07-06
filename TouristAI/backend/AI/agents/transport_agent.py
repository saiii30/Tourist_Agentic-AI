import os
import json
import requests
from datetime import datetime
from rag_service import get_answer, save_to_rag, client
import re


RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BASE_URL = "https://irctc1.p.rapidapi.com"


# -----------------------------
# Flight Search
# -----------------------------
def get_flights(source, destination, date):

    # This is a placeholder. Replace with a real flight API if available.
    # url = "https://example-flight-api.p.rapidapi.com/search"

    # headers = {
    #     "X-RapidAPI-Key": RAPIDAPI_KEY,
    #     "X-RapidAPI-Host": "example-flight-api.p.rapidapi.com"
    # }

    params = {
        "source": source,
        "destination": destination,
        "date": date
    }

    # try:
    #     response = requests.get(
    #         url,
    #         headers=headers,
    #         params=params,
    #         timeout=20
    #     )

    #     if response.status_code == 200:
    #         return response.json()

    # except Exception as e:
    #     print(f"Flight API error: {e}")

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
    
    # Otherwise, look it up via the API
    url = f"{BASE_URL}/findstations.php"
    headers = {
        "x-rapidapi-host": "indianrailways.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    params = {"station": name}
    
    try:
        print(f"🔍 Calling API: {url} with params: {params}")
        res = requests.get(url, headers=headers, params=params)
        print(f"🔍 API Response Status: {res.status_code}")
        
        if res.status_code != 200:
            print(f"⚠️ Station lookup failed for '{name}': {res.status_code}")
            print(f"🔍 Response: {res.text[:300]}")
            # Try using the cleaned name as a fallback
            if cleaned_name != name.upper():
                print(f"🔍 Trying with cleaned name '{cleaned_name}'...")
                params["station"] = cleaned_name
                res = requests.get(url, headers=headers, params=params)
                if res.status_code == 200:
                    data = res.json()
                    print(f"🔍 API Response Data: {data}")
                    if "Station" in data and len(data["Station"]) > 0:
                        code = data["Station"][0]["StationCode"]
                        print(f"🔍 Found code via API: {code}")
                        return code
            return None
        
        data = res.json()
        print(f"🔍 API Response Data: {data}")
        if "Station" in data and len(data["Station"]) > 0:
            code = data["Station"][0]["StationCode"]
            print(f"🔍 Found code via API: {code}")
            return code
        return None
    except Exception as e:
        print(f"❌ Station lookup error for '{name}': {e}")
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
# Train Search
# -----------------------------
def get_trains(source, destination, date):
    print(f"Searching trains from {source} to {destination} on {date}...")

    if not RAPIDAPI_KEY:
        print("⚠️ Missing RAPIDAPI_KEY")
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

    url = f"{BASE_URL}/api/v3/trainBetweenStations"
    headers = {
        "x-rapidapi-host": "irctc1.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY,
        "Content-Type": "application/json"
    }
    params = {
        "fromStationCode": from_code,
        "toStationCode": to_code,
        "dateOfJourney": formatted_date
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"🔍 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Train API call successful.")
            return response.json()
        elif response.status_code == 429:
            print("⚠️ API quota exceeded")
            return {"message": "Quota exceeded"}
        else:
            print(f"⚠️ API returned status code {response.status_code}")
            print(f"🔍 Response: {response.text[:300]}")
            return None
    except Exception as e:
        print(f"❌ Train API error: {e}")
        return None

# -----------------------------
# Bus Search
# -----------------------------
def get_buses(source, destination, date):

    # This is a placeholder. Replace with a real bus API if available.
    # url = "https://example-bus-api.p.rapidapi.com/search"

    # headers = {
    #     "X-RapidAPI-Key": RAPIDAPI_KEY,
    #     "X-RapidAPI-Host": "example-bus-api.p.rapidapi.com"
    # }

    params = {
        "source": source,
        "destination": destination,
        "date": date
    }

    # try:
    #     response = requests.get(
    #         url,
    #         headers=headers,
    #         params=params,
    #         timeout=20
    #     )

    #     if response.status_code == 200:
    #         return response.json()
    # except Exception as e:
    #     print(f"Bus API error: {e}")

    return None


# -----------------------------
# Format Response
# -----------------------------
def format_transport(flights, trains, buses, date=""):
    output = []

    # Trains - format as numbered lists for PlaceCard component
    if trains:
        # Handle IRCTC1 API response structure: {status: true, data: [...]}
        if isinstance(trains, dict) and "data" in trains and isinstance(trains["data"], list) and len(trains["data"]) > 0:
            for idx, t in enumerate(trains["data"][:5], 1):
                train_name = t.get('train_name', 'Unknown')
                train_number = t.get('train_number', '')
                from_name = t.get('from_station_name', '')
                to_name = t.get('to_station_name', '')
                from_code = t.get('from', '')
                to_code = t.get('to', '')
                departure = t.get('from_std', '')
                arrival = t.get('to_std', '')
                duration = t.get('duration', '')
                train_type = t.get('train_type', '')
                class_type = t.get('class_type', [])
                
                # Format duration (already in hours:minutes format from API)
                duration_str = duration
                
                # Format class types
                classes_str = ", ".join(class_type) if isinstance(class_type, list) else str(class_type)
                
                # IRCTC booking URL with date
                irctc_url = f"https://www.irctc.co.in/nget/train-search?fromStation={from_code}&toStation={to_code}&journeyDate={date}"
                
                output.append(f"{idx}. **{train_name} ({train_number})**")
                output.append(f"- 🚂 Type: {train_type}")
                output.append(f"- 📍 From: {from_name} ({from_code})")
                output.append(f"- 📍 To: {to_name} ({to_code})")
                output.append(f"- ⏰ Departure: {departure}")
                output.append(f"- ⏰ Arrival: {arrival}")
                output.append(f"- ⏱️ Duration: {duration_str}")
                if classes_str:
                    output.append(f"- 🎫 Classes: {classes_str}")
                # Add run days
                run_days = t.get('run_days', [])
                if run_days and isinstance(run_days, list):
                    output.append(f"- 📅 Runs: {', '.join(run_days)}")
                # Add train date
                train_date = t.get('train_date', '')
                if train_date:
                    output.append(f"- 🗓️ Date: {train_date}")
                # Add special train flag
                special_train = t.get('special_train', False)
                if special_train:
                    output.append(f"- ⭐ Special Train")
                output.append(f"[Visit Website]({irctc_url})")
                output.append("")
        # Handle list response (direct list of trains)
        elif isinstance(trains, list) and len(trains) > 0:
            for idx, t in enumerate(trains[:5], 1):
                train_name = t.get('train_name', t.get('trainName', 'Unknown'))
                train_number = t.get('train_number', t.get('trainNumber', ''))
                from_name = t.get('from_station_name', t.get('fromStationName', ''))
                to_name = t.get('to_station_name', t.get('toStationName', ''))
                departure = t.get('from_time', t.get('departureTime', ''))
                arrival = t.get('to_time', t.get('arrivalTime', ''))
                duration = t.get('duration', '')
                
                output.append(f"{idx}. **{train_name} ({train_number})**")
                output.append(f"- 📍 From: {from_name}")
                output.append(f"- 📍 To: {to_name}")
                output.append(f"- ⏰ Departure: {departure}")
                output.append(f"- ⏰ Arrival: {arrival}")
                output.append(f"- ⏱️ Duration: {duration}")
                output.append("")
        elif isinstance(trains, dict) and "message" in trains:
            output.append(trains["message"])
        else:
            output.append("No train data found in response")
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
    # flights = get_flights(source, destination, date)
    trains = get_trains(source, destination, date)
    # buses = get_buses(source, destination, date)

    # If all APIs fail, use a final LLM fallback
    # if not flights and not trains and not buses:
    if not trains:
        print("⚠️ All transport APIs failed. Falling back to Groq LLM.")
        return get_answer(question) # This will call Groq and save to RAG

    # answer = format_transport(flights, trains, buses)
    answer = format_transport(None, trains, None)

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
