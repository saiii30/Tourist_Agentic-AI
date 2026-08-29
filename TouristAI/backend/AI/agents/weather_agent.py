import os
import urllib.request
import urllib.parse
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from rag_service import client

# Load environment variables from possible locations to ensure API keys are populated
for env_path in [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
    os.path.abspath(os.path.join(os.getcwd(), ".env")),
    os.path.abspath(os.path.join(os.getcwd(), "backend", ".env")),
]:
    if os.path.exists(env_path):
        load_dotenv(env_path)

def extract_city(question: str) -> str:
    prompt = (
        "Extract the primary city or location name from the following user query. "
        "Return ONLY the city name in plain text (e.g. 'Chennai', 'Madurai', 'Ooty') and absolutely nothing else. "
        "Do not include punctuation, quotes, or markdown. "
        "If no specific city or location is mentioned, return the word 'None' exactly.\n\n"
        f"Query: {question}"
    )
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        city = response.choices[0].message.content.strip().strip("'\"")
        # Handle some cases where LLM might return empty or full sentences
        if len(city) > 40 or not city or city.lower() == "none":
            return "None"
        return city
    except Exception as e:
        print(f"Error extracting city: {e}")
        return "None"

def get_live_weather(city: str) -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        print("OPENWEATHER_API_KEY not found in environment.")
        return None

    encoded_city = urllib.parse.quote(city)
    url = f"https://api.openweathermap.org/data/2.5/weather?q={encoded_city}&appid={api_key}&units=metric"
    
    try:
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
    except Exception as e:
        print(f"Error fetching live weather from OpenWeather API for '{city}': {e}")
        return None

def get_live_forecast(city: str) -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return None

    encoded_city = urllib.parse.quote(city)
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={encoded_city}&appid={api_key}&units=metric"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=6) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Error fetching live forecast from OpenWeather API for '{city}': {e}")
        return None

def get_mock_weather(city: str) -> dict:
    # Deterministic mock weather using seed from city name to keep it consistent
    try:
        random.seed(city.lower())
    except Exception:
        pass
    
    conditions = [
        {"main": "Clear", "desc": "clear sky"},
        {"main": "Clouds", "desc": "scattered clouds"},
        {"main": "Clouds", "desc": "broken clouds"},
        {"main": "Rain", "desc": "light rain"},
        {"main": "Rain", "desc": "moderate rain"},
        {"main": "Thunderstorm", "desc": "thunderstorm with light rain"},
        {"main": "Drizzle", "desc": "light intensity drizzle"}
    ]
    
    condition = random.choice(conditions)
    # Warm climates generally, with colder weather for hill stations like Ooty
    is_hill_station = any(h in city.lower() for h in ["ooty", "kodaikanal", "coonoor", "yercaud", "munnar"])
    if is_hill_station:
        temp = round(random.uniform(12.0, 20.0), 1)
    else:
        temp = round(random.uniform(25.0, 35.0), 1)
        
    feels_like = round(temp + random.uniform(1.0, 4.0), 1)
    humidity = random.randint(50, 85)
    wind_speed = round(random.uniform(2.0, 8.0), 1)
    
    # Reset random seed
    random.seed(None)
    
    return {
        "name": city.title(),
        "main": {
            "temp": temp,
            "feels_like": feels_like,
            "humidity": humidity,
            "pressure": 1010
        },
        "weather": [
            {
                "main": condition["main"],
                "description": condition["desc"]
            }
        ],
        "wind": {
            "speed": wind_speed
        }
    }

def get_mock_forecast(city: str, days: int = 5) -> list[dict]:
    try:
        random.seed(f"{city.lower()}-forecast")
    except Exception:
        pass

    is_hill_station = any(h in city.lower() for h in ["ooty", "kodaikanal", "coonoor", "yercaud", "munnar"])
    daily = []
    for idx in range(days):
        condition = random.choice([
            ("Clear", "clear sky"),
            ("Clouds", "partly cloudy"),
            ("Rain", "light rain"),
            ("Rain", "moderate rain"),
            ("Thunderstorm", "thunderstorm"),
        ])
        base_temp = random.uniform(14, 23) if is_hill_station else random.uniform(27, 36)
        daily.append({
            "day": idx + 1,
            "date": (datetime.now() + timedelta(days=idx)).strftime("%Y-%m-%d"),
            "main": condition[0],
            "description": condition[1],
            "temp": round(base_temp, 1),
            "min_temp": round(base_temp - random.uniform(2, 4), 1),
            "max_temp": round(base_temp + random.uniform(2, 5), 1),
            "humidity": random.randint(45, 90),
            "wind_speed": round(random.uniform(2, 9), 1),
            "rain_probability": random.randint(50, 90) if condition[0] in {"Rain", "Thunderstorm"} else random.randint(0, 35),
        })
    random.seed(None)
    return daily

def summarize_live_forecast(forecast_data: dict, days: int = 5) -> list[dict]:
    if not forecast_data or not forecast_data.get("list"):
        return []

    grouped = {}
    for item in forecast_data.get("list", []):
        date_key = item.get("dt_txt", "").split(" ")[0]
        if not date_key:
            continue
        grouped.setdefault(date_key, []).append(item)

    daily = []
    for idx, (date_key, items) in enumerate(list(grouped.items())[:days], 1):
        temps = [entry.get("main", {}).get("temp") for entry in items if entry.get("main", {}).get("temp") is not None]
        humidities = [entry.get("main", {}).get("humidity") for entry in items if entry.get("main", {}).get("humidity") is not None]
        winds = [entry.get("wind", {}).get("speed") for entry in items if entry.get("wind", {}).get("speed") is not None]
        conditions = [entry.get("weather", [{}])[0] for entry in items]
        rainy = [cond for cond in conditions if any(k in str(cond.get("main", "")).lower() for k in ["rain", "storm", "drizzle"])]
        selected = rainy[0] if rainy else conditions[len(conditions) // 2] if conditions else {}
        pop = max([entry.get("pop", 0) for entry in items] or [0])
        daily.append({
            "day": idx,
            "date": date_key,
            "main": selected.get("main", "Clear"),
            "description": selected.get("description", "clear sky"),
            "temp": round(sum(temps) / len(temps), 1) if temps else 28,
            "min_temp": round(min(temps), 1) if temps else 25,
            "max_temp": round(max(temps), 1) if temps else 32,
            "humidity": round(sum(humidities) / len(humidities)) if humidities else 60,
            "wind_speed": round(max(winds), 1) if winds else 3,
            "rain_probability": round(pop * 100),
        })
    return daily

def outdoor_score(day: dict) -> int:
    score = 100
    main = str(day.get("main", "")).lower()
    desc = str(day.get("description", "")).lower()
    temp = float(day.get("max_temp") or day.get("temp") or 30)
    humidity = float(day.get("humidity") or 60)
    rain_probability = float(day.get("rain_probability") or 0)
    wind = float(day.get("wind_speed") or 0)

    if any(k in main or k in desc for k in ["thunderstorm", "storm"]):
        score -= 45
    elif any(k in main or k in desc for k in ["rain", "drizzle"]):
        score -= 28
    score -= max(0, rain_probability - 30) * 0.35
    if temp >= 38:
        score -= 30
    elif temp >= 34:
        score -= 18
    elif temp <= 14:
        score -= 12
    if humidity >= 85:
        score -= 10
    if wind >= 12:
        score -= 8
    return int(max(5, min(100, round(score))))

def build_weather_intelligence(city: str, current: dict, forecast: list[dict], is_mock: bool) -> dict:
    temp = current["main"]["temp"]
    humidity = current["main"]["humidity"]
    wind = current["wind"]["speed"]
    main_cond = current["weather"][0].get("main", "Clear")
    desc = current["weather"][0].get("description", "clear sky")
    feels_like = current["main"]["feels_like"]

    alerts = []
    packing = set()
    health = []
    itinerary_changes = []
    best_times = []

    for item in forecast:
        score = outdoor_score(item)
        item["outdoor_score"] = score
        item["activity_advice"] = "Great for sightseeing" if score >= 75 else "Prefer morning/evening outdoor plans" if score >= 50 else "Prefer indoor attractions"
        main = str(item.get("main", "")).lower()
        max_temp = item.get("max_temp", item.get("temp", temp))
        rain_probability = item.get("rain_probability", 0)

        if "rain" in main or "storm" in main or rain_probability >= 60:
            alerts.append({
                "type": "rain",
                "day": item["day"],
                "title": "Rain may affect outdoor plans",
                "message": "Carry umbrella or raincoat and prefer museums, galleries, cafes, and shopping blocks.",
                "severity": "high" if "storm" in main or rain_probability >= 75 else "medium",
            })
            packing.update(["Umbrella", "Raincoat", "Waterproof footwear"])
            itinerary_changes.append({
                "day": item["day"],
                "issue": "Rain expected",
                "suggestion": "Move parks, beaches, viewpoints, and walking tours to a clearer slot. Use museums, art galleries, temples with covered queues, cafes, or malls during rain.",
            })

        if max_temp >= 35:
            alerts.append({
                "type": "heat",
                "day": item["day"],
                "title": "High temperature expected",
                "message": "Avoid long outdoor activity from 12 PM to 4 PM.",
                "severity": "medium",
            })
            packing.update(["Sunscreen", "Cap or hat", "Sunglasses", "Reusable water bottle"])
            health.append("High heat: hydrate often and schedule outdoor visits early morning or after 5 PM.")

        if item.get("min_temp", temp) <= 16:
            packing.add("Light jacket")
            health.append("Cool evening/night temperature: carry a light jacket.")

        best_times.append({
            "day": item["day"],
            "best_time": "7 AM-10 AM" if max_temp >= 32 else "9 AM-12 PM",
            "avoid": "12 PM-4 PM" if max_temp >= 32 else "Heavy rain slots" if rain_probability >= 60 else "None",
            "reason": "Heat management" if max_temp >= 32 else "Rain risk" if rain_probability >= 60 else "Comfortable conditions",
        })

    if humidity >= 80:
        health.append("High humidity: wear breathable clothes and carry tissues or hand towels.")
        packing.add("Breathable cotton clothes")
    if wind >= 10:
        health.append("Windy conditions: secure loose items during viewpoints or boating.")
    if temp >= 32:
        packing.update(["Cotton clothes", "Sunscreen", "Water bottle"])
    if any(k in desc.lower() or k in main_cond.lower() for k in ["rain", "storm", "drizzle"]):
        packing.update(["Umbrella", "Quick-dry clothes"])

    route_advice = []
    if any(alert["type"] == "rain" for alert in alerts):
        route_advice.append("Road trips may face slower traffic and slippery roads near rain-affected stretches.")
    if any(alert["type"] == "heat" for alert in alerts):
        route_advice.append("For road travel, keep water in the vehicle and avoid long midday walking stops.")
    if not route_advice:
        route_advice.append("No major weather disruption expected for local travel.")

    current_score = outdoor_score({
        "main": main_cond,
        "description": desc,
        "temp": temp,
        "max_temp": temp,
        "humidity": humidity,
        "wind_speed": wind,
        "rain_probability": 70 if "rain" in desc.lower() else 10,
    })

    return {
        "location": city,
        "current": {
            "temp": temp,
            "feels_like": feels_like,
            "humidity": humidity,
            "wind_speed": wind,
            "description": desc,
            "main": main_cond,
            "uv_index": 8 if temp >= 34 else 5 if temp >= 28 else 3,
            "air_quality": "Moderate" if humidity >= 80 else "Good",
            "updated": "just now" if not is_mock else "simulated",
        },
        "forecast": forecast,
        "outdoor_score": current_score,
        "packing": sorted(packing)[:8],
        "alerts": alerts[:6],
        "best_times": best_times,
        "health_advice": list(dict.fromkeys(health))[:5],
        "route_advice": route_advice,
        "itinerary_suggestions": itinerary_changes[:5],
        "source": "mock" if is_mock else "openweather",
    }

def weather_agent(question: str, city: str = "None") -> dict:
    if city == "None" or not city or str(city).strip() == "" or str(city).lower() == "none":
        from services.rules import common_rules
        extracted_city = common_rules.extract_city(question)
        if not extracted_city or extracted_city == "None":
            extracted_city = extract_city(question)
        city = extracted_city if extracted_city and extracted_city != "None" else "Chennai"
        
    # Get weather (live first, then mock)
    weather_data = get_live_weather(city)
    forecast_data = get_live_forecast(city)
    is_mock = False
    
    if not weather_data:
        weather_data = get_mock_weather(city)
        is_mock = True

    forecast = summarize_live_forecast(forecast_data, days=5) if forecast_data else []
    if not forecast:
        forecast = get_mock_forecast(city, days=5)
        
    # Extract weather parameters
    weather_desc = weather_data["weather"][0]["description"]
    main_cond = weather_data["weather"][0].get("main", "Clear")
    temp = weather_data["main"]["temp"]
    feels_like = weather_data["main"]["feels_like"]
    humidity = weather_data["main"]["humidity"]
    wind = weather_data["wind"]["speed"]
    city_name = weather_data["name"]
    
    # Rule Engine: Determine recommendations based on weather parameters
    clothing = ""
    sightseeing = ""
    tip = ""
    
    cond_lower = weather_desc.lower()
    main_lower = main_cond.lower()
    
    # 1. Check for precipitation (Rain / Drizzle / Thunderstorm)
    if any(keyword in cond_lower or keyword in main_lower for keyword in ["rain", "drizzle", "thunderstorm", "storm", "snow"]):
        clothing = "Waterproof clothing, sturdy footwear, and carrying an umbrella or raincoat are essential."
        sightseeing = "Outdoor activities might be disrupted. Consider indoor attractions (museums, art galleries, cafes) or shopping malls."
        tip = "Keep track of local weather updates and avoid travel to areas prone to waterlogging."
    
    # 2. Temperature-based rules
    elif temp < 15.0:
        clothing = "Carry warm layers, a thick jacket, gloves, and a woolen cap, especially for early mornings and nights."
        sightseeing = "Ideal for nature walks, scenic drives, or hot beverages in cozy cafes. Viewpoints are best visited when fog clears."
        tip = "Start your day a bit later as mornings can be very cold."
    elif temp < 22.0:
        clothing = "A light sweater, shawl, or sweatshirt will keep you comfortable during cooler hours."
        sightseeing = "Perfect weather for sightseeing! Great time for hiking, visiting outdoor monuments, and street walks."
        tip = "Enjoy outdoor activities without worrying about heat; keep sunscreen handy as the sun can still be bright."
    elif temp > 30.0:
        clothing = "Wear loose, light-colored, breathable cotton clothes. Don't forget sunglasses and a wide-brimmed hat."
        sightseeing = "Plan outdoor sightseeing for early morning or late evening. Spend the hot afternoon hours indoors or resting."
        tip = "Stay hydrated! Drink plenty of water and apply high-SPF sunscreen regularly."
    else:  # Moderate/Pleasant: 22°C to 30°C
        clothing = "Comfortable everyday casual clothes. A light cover-up might be useful for late evening breeze."
        sightseeing = "Excellent conditions for all outdoor activities, sightseeing, and exploring the city on foot."
        tip = "A perfect time for photography and visiting parks or gardens."

    # Wind and humidity refinements
    if wind > 10.0:
        tip += " It is quite windy, so secure loose items."
    if humidity > 80:
        tip += " High humidity might make it feel warmer and cause sweating; carry tissues or hand towels."

    intelligence = build_weather_intelligence(city_name, weather_data, forecast, is_mock)
    alert_line = ""
    if intelligence["alerts"]:
        top_alert = intelligence["alerts"][0]
        alert_line = f"\n\n⚠️ **{top_alert['title']}**: {top_alert['message']}"
    forecast_lines = "\n".join(
        f"- **Day {day['day']} ({day['date']})**: {day['description'].title()}, {day['min_temp']}°C-{day['max_temp']}°C, outdoor score {day['outdoor_score']}/100"
        for day in intelligence["forecast"][:5]
    )
    packing_line = ", ".join(intelligence["packing"]) if intelligence["packing"] else "Regular comfortable travel essentials"

    # Format the final response
    answer = (
        f"Currently in **{city_name}**, the weather is **{temp}°C** (feels like **{feels_like}°C**) with **{weather_desc}**.\n"
        f"- **Humidity:** {humidity}%\n"
        f"- **Wind Speed:** {wind} m/s\n\n"
        f"**Travel Advice:**\n"
        f"- 👕 **Clothing:** {clothing}\n"
        f"- 🗺 **Sightseeing:** {sightseeing}\n"
        f"- 💡 **Tip:** {tip}\n\n"
        f"**Trip Weather Intelligence:**\n"
        f"- 🚶 **Outdoor Score:** {intelligence['outdoor_score']}/100\n"
        f"- 🎒 **Packing:** {packing_line}\n"
        f"- 📅 **Forecast:**\n{forecast_lines}"
        f"{alert_line}"
    )
    
    # Append mock warning if applicable
    if is_mock:
        answer += "\n\n*(Note: Displaying simulated weather data. To enable live weather, please configure `OPENWEATHER_API_KEY` in your `.env` file.)*"
        
    return {
        "text": answer,
        "data": {
            "temp": temp,
            "feels_like": feels_like,
            "description": weather_desc,
            "main": main_cond,
            "humidity": humidity,
            "wind_speed": wind,
            "forecast": intelligence["forecast"],
            "weather_intelligence": intelligence,
            "packing": intelligence["packing"],
            "alerts": intelligence["alerts"],
            "outdoor_score": intelligence["outdoor_score"],
            "itinerary_suggestions": intelligence["itinerary_suggestions"],
        }
    }
