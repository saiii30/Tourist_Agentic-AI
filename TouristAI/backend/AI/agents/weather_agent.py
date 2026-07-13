import os
import urllib.request
import urllib.parse
import json
import random
from rag_service import client

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
            model="llama-3.1-8b-instant",
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

def weather_agent(question: str, city: str = "None") -> str:
    if city == "None":
        return "I need to know which city or destination you are planning to visit to fetch the weather forecast."
        
    # Get weather (live first, then mock)
    weather_data = get_live_weather(city)
    is_mock = False
    
    if not weather_data:
        weather_data = get_mock_weather(city)
        is_mock = True
        
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

    # Format the final response
    answer = (
        f"Currently in **{city_name}**, the weather is **{temp}°C** (feels like **{feels_like}°C**) with **{weather_desc}**.\n"
        f"- **Humidity:** {humidity}%\n"
        f"- **Wind Speed:** {wind} m/s\n\n"
        f"**Travel Advice:**\n"
        f"- 👕 **Clothing:** {clothing}\n"
        f"- 🗺 **Sightseeing:** {sightseeing}\n"
        f"- 💡 **Tip:** {tip}"
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
            "wind_speed": wind
        }
    }
