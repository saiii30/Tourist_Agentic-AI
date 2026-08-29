import os
import json
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables from possible locations to ensure API keys are populated
for env_path in [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
    os.path.abspath(os.path.join(os.getcwd(), ".env")),
    os.path.abspath(os.path.join(os.getcwd(), "backend", ".env")),
]:
    if os.path.exists(env_path):
        load_dotenv(env_path)

from rag_service import client

def generate_voice_notifications_llm(
    city: str,
    days: int,
    itinerary_items: list,
    hotels: list,
    restaurants: list,
    nearby: list,
    weather: dict,
    calendar_synced: bool = False
) -> list:
    """
    Calls the LLM (Groq) to analyze the full trip context and generate travel companion notifications.
    """
    
    # Structure inputs for prompt
    itinerary_summary = []
    for item in itinerary_items:
        itinerary_summary.append({
            "day": item.get("day", 1),
            "start_time": item.get("start_time", "09:00"),
            "end_time": item.get("end_time", "10:00"),
            "activity": item.get("activity", ""),
            "location": item.get("location", ""),
            "category": item.get("category", "")
        })

    weather_desc = weather.get("description", "pleasant weather") if weather else "pleasant weather"
    weather_temp = weather.get("temp", 26.0) if weather else 26.0
    
    prompt = f"""You are TouristAI's Smart Voice Travel Assistant and Companion.
Your task is to analyze the complete trip details for a {days}-day trip to {city.title()} and generate a list of proactive travel alerts and notifications.

Trip details:
- Destination: {city.title()}
- Duration: {days} days
- Itinerary Schedule: {json.dumps(itinerary_summary, indent=2)}
- Weather Forecast: {weather_temp}°C with {weather_desc}
- Recommended Hotels: {json.dumps([h.get("name") for h in hotels] if hotels else [], indent=2)}
- Recommended Restaurants: {json.dumps([r.get("name") for r in restaurants] if restaurants else [], indent=2)}
- Nearby Attractions: {json.dumps([p.get("name") for p in nearby] if nearby else [], indent=2)}
- Google Calendar Synced: {calendar_synced}

Responsibilities:
1. Analyze the trip details to construct context-aware notifications.
2. Avoid duplicates: Do not generate redundant notifications or repeat the same weather warnings.
3. Be highly concise: Maximum 2 short sentences per notification. Enforce a spoken duration of 8 to 12 seconds.
4. Sound natural: Avoid robotic wording. Always write out numbers, times, and abbreviations (e.g. "thirty minutes" instead of "30 mins", "two PM" instead of "2 PM", "Celsius" instead of "C").
5. Do NOT fabricate information. Use only the provided names, locations, and weather.

You must generate notifications for the following triggers and categories:
- trip_created: A welcome notification celebrating the trip generation.
- calendar_saved (only if calendar_synced is True): A notification confirming Google Calendar sync.
- 1_day_before: Day-before reminders (e.g., preparation, weather guidelines).
- trip_started: Opening day greeting when starting the journey.
- 30_minutes_before: Reminders for itinerary activities, hotels, and restaurant stops.
- meal_time: Lunch or dinner recommendations.
- evening: End-of-day wrap-up notifications.
- immediate: High priority alerts (e.g. if the forecast indicates rain, storm, or extreme weather warnings).

Return a valid JSON object ONLY containing a key "notifications" which is a list of notification dictionaries. Each notification must conform strictly to the following schema:
{{
  "id": "unique_string_id",
  "type": "weather" | "activity" | "hotel" | "restaurant" | "nearby" | "calendar" | "trip_start" | "trip_end" | "packing" | "general",
  "source": "weather" | "itinerary" | "calendar" | "hotel" | "restaurant" | "nearby",
  "priority": "critical" | "high" | "medium" | "low",
  "trigger": "immediate" | "trip_created" | "trip_started" | "1_day_before" | "2_hours_before" | "30_minutes_before" | "arrival" | "departure" | "meal_time" | "evening" | "calendar_saved",
  "event_time": "ISO format string or time in HH:MM representing the itinerary event time (or null if none)",
  "title": "Short title text (e.g., 'Rain Expected')",
  "text": "Short screen description text (e.g., 'Carry an umbrella before visiting Sirumalai.')",
  "voice": "The conversational script spoken by the voice assistant (e.g., 'Hello! Rain is expected this afternoon. Please carry an umbrella before visiting Sirumalai View Point.')",
  "play_voice": true,
  "spoken": false,
  "status": "pending",
  "action": {{ "label": "String button text", "type": "weather" | "hotel" | "restaurant" | "itinerary" | "calendar" | "maps" }} or null
}}

Respond ONLY with valid JSON. Do not include markdown code block syntax (like ```json) or any conversational text around the JSON. Output raw JSON object starting with {{ and ending with }}.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        
        # Clean up any potential markdown wraps
        if content.startswith("```json"):
            content = content.split("```json", 1)[1]
        if content.endswith("```"):
            content = content.rsplit("```", 1)[0]
        content = content.strip()
        
        data = json.loads(content)
        return data.get("notifications", [])
    except Exception as e:
        print(f"[Error Voice Agent] Failed to generate notifications: {e}")
        # Return a robust programmatic fallback list of notifications
        return get_fallback_notifications(city, itinerary_items, hotels, restaurants, nearby, weather, calendar_synced)


def get_fallback_notifications(city, itinerary_items, hotels, restaurants, nearby, weather, calendar_synced):
    """
    Programmatic fallback generator to ensure voice notifications are always available even if LLM fails or keys are missing.
    """
    notifications = []
    
    # 1. Trip Created
    notifications.append({
        "id": f"gen_created_{city.lower()}",
        "type": "general",
        "source": "itinerary",
        "priority": "medium",
        "trigger": "trip_created",
        "event_time": None,
        "title": "Trip Created",
        "text": f"Your trip to {city.title()} is successfully planned.",
        "voice": f"Your travel companion is ready. Your trip to {city.title()} has been successfully planned.",
        "play_voice": True,
        "spoken": False,
        "status": "pending",
        "action": {"label": "View Itinerary", "type": "itinerary"}
    })
    
    # 2. Calendar saved sync status
    if calendar_synced:
        notifications.append({
            "id": f"gen_cal_{city.lower()}",
            "type": "calendar",
            "source": "calendar",
            "priority": "medium",
            "trigger": "calendar_saved",
            "event_time": None,
            "title": "Google Calendar Synced",
            "text": "Itinerary added to Google Calendar.",
            "voice": "Your itinerary is successfully synced with Google Calendar. You will receive notifications before every activity.",
            "play_voice": True,
            "spoken": False,
            "status": "pending",
            "action": {"label": "Open Calendar", "type": "calendar"}
        })

    # 3. Weather check
    desc = weather.get("description", "clear sky") if weather else "clear sky"
    temp = weather.get("temp", 26.0) if weather else 26.0
    is_rainy = "rain" in desc or "storm" in desc or "drizzle" in desc
    notifications.append({
        "id": f"gen_weather_{city.lower()}",
        "type": "weather",
        "source": "weather",
        "priority": "high" if is_rainy else "low",
        "trigger": "immediate",
        "event_time": None,
        "title": "Weather Warning" if is_rainy else "Weather Update",
        "text": "Carry an umbrella." if is_rainy else f"Enjoy the {temp} degrees weather.",
        "voice": f"Currently in {city.title()} the weather is {temp} degrees Celsius with {desc}. Please carry an umbrella before visiting outdoor sights." if is_rainy else f"The weather in {city.title()} is currently {temp} degrees Celsius with {desc}. Perfect conditions for exploring.",
        "play_voice": True,
        "spoken": False,
        "status": "pending",
        "action": {"label": "View Forecast", "type": "weather"}
    })

    # 4. Activity alerts based on itinerary items
    if itinerary_items:
        for idx, item in enumerate(itinerary_items[:4]):
            activity = item.get("activity", "Sightseeing")
            time_str = item.get("start_time", "09:00")
            day = item.get("day", 1)
            
            # Map category to source
            source = "itinerary"
            if item.get("hotel"): source = "hotel"
            elif item.get("restaurant"): source = "restaurant"
            
            notifications.append({
                "id": f"gen_activity_day{day}_{idx}",
                "type": "activity",
                "source": source,
                "priority": "medium",
                "trigger": "30_minutes_before",
                "event_time": f"Day {day} at {time_str}",
                "title": f"Upcoming Activity",
                "text": f"Visit {activity} in thirty minutes.",
                "voice": f"Your next activity begins in thirty minutes. It is time to visit {activity}.",
                "play_voice": True,
                "spoken": False,
                "status": "pending",
                "action": {"label": "Open Maps", "type": "maps"}
            })

    return notifications


def generate_voice_notifications(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph Node implementation for Smart Voice Notification Agent.
    """
    from supervisor import get_guided_state
    g_state = get_guided_state()
    city = g_state.get("destination", state.get("city", "None"))
    days = int(g_state.get("days", state.get("days", 3)))
    trip_id = g_state.get("trip_id")
    
    # Read itinerary items
    cached_items_json = g_state.get("last_itinerary_items")
    itinerary_items = []
    if cached_items_json:
        try:
            itinerary_items = json.loads(cached_items_json)
        except:
            pass
            
    # Check calendar sync status
    calendar_synced = False
    if trip_id:
        from services.calendar_service import CalendarService
        cal_service = CalendarService()
        events = cal_service.repo.get_calendar_events(trip_id)
        if events:
            calendar_synced = True

    # Generate using LLM
    notifications = generate_voice_notifications_llm(
        city=city,
        days=days,
        itinerary_items=itinerary_items,
        hotels=state.get("hotels_data", []),
        restaurants=state.get("restaurants_data", []),
        nearby=state.get("nearby_data", []),
        weather=state.get("weather_data", {}),
        calendar_synced=calendar_synced
    )
    
    # Apply notification scheduler logic to process, sort, and priority-rank notifications
    from services.notification_scheduler import NotificationSchedulerService
    scheduled_notifications = NotificationSchedulerService.schedule(notifications, itinerary_items)
    
    return {
        "notifications": scheduled_notifications
    }
