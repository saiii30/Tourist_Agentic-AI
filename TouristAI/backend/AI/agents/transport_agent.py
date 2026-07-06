import os
import json
import requests
from rag_service import get_answer, save_to_rag, client


RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")


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
# Train Search
# -----------------------------
def get_trains(source, destination, date):

    print(f"Searching trains from {source} to {destination} on {date}...")

    if not RAPIDAPI_KEY:
        print("⚠️ RAPIDAPI_KEY not found. Skipping train search.")
        return None

    url = "https://irctc1.p.rapidapi.com/api/v1/train/searchTrain"

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "irctc1.p.rapidapi.com"
    }
    
    # The API expects station codes. We'll pass full names and let it handle it.
    # A more robust solution would map city names to station codes first.
    params = {
        "fromCity": source,
        "toCity": destination,
        "date": date
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=20
        )

        if response.status_code == 200:
            print("✅ Train API call successful.")
            return response.json()

    except Exception as e:
        print(f"Train API error: {e}")

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
def format_transport(flights, trains, buses):

    output = []

    # Flights
    output.append("✈️ Flights")
    output.append("--------------------------------")

    if flights and flights.get("data"):
        for item in flights["data"][:5]:
            # Customize flight output based on actual API response structure
            output.append(json.dumps(item, indent=2))
    else:
        output.append("No Flights Found")

    output.append("")


    # Trains
    output.append("🚆 Trains")
    output.append("--------------------------------")

    if trains:

        if trains.get("status") and trains.get("data"):
            for train in trains["data"][:5]:
                train_line = (
                    f"**{train.get('train_name')} ({train.get('train_number')})**\n"
                    f"  - Departs: {train.get('from_station_name')} at {train.get('from_time')}\n"
                    f"  - Arrives: {train.get('to_station_name')} at {train.get('to_time')}\n"
                    f"  - Duration: {train.get('duration')}\n"
                    f"  - Classes: {', '.join(train.get('class_type', []))}"
                )
                output.append(train_line)
        elif "message" in trains:
            output.append(trains["message"])

    else:
        output.append("No Trains Found")

    output.append("")

    # Buses
    output.append("🚌 Buses")
    output.append("--------------------------------")

    if buses:
        if buses.get("data"):
            for item in buses["data"][:5]:
                # Customize bus output based on actual API response structure
                output.append(json.dumps(item, indent=2))
    else:
        output.append("No Buses Found")

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
    flights = get_flights(source, destination, date)
    trains = get_trains(source, destination, date)
    buses = get_buses(source, destination, date)

    # If all APIs fail, use a final LLM fallback
    if not flights and not trains and not buses:
        print("⚠️ All transport APIs failed. Falling back to Groq LLM.")
        return get_answer(question) # This will call Groq and save to RAG

    answer = format_transport(flights, trains, buses)

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

