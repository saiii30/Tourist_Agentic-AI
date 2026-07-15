import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

def calculate_haversine(lat1: Optional[float], lon1: Optional[float], lat2: Optional[float], lon2: Optional[float]) -> float:
    """
    Computes distance in kilometers between two lat/lng coordinates.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0.0
    try:
        R = 6371.0  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    except Exception:
        return 0.0

def estimate_travel(distance_km: float) -> tuple[str, str]:
    """
    Estimates travel time and transport mode based on distance.
    """
    if distance_km == 0.0:
        return "0 mins", "Stay"
    if distance_km <= 1.0:
        mins = int(distance_km * 12)
        return f"{max(1, mins)} mins", "Walking"
    elif distance_km <= 5.0:
        mins = int(distance_km * 4)
        return f"{max(5, mins)} mins", "Auto Rickshaw"
    else:
        mins = int(distance_km * 3)
        return f"{max(10, mins)} mins", "Cab"

class CalendarBuilder:
    @staticmethod
    def build_itinerary(
        city: str,
        start_date_str: str,
        days: int,
        budget: str,
        travel_style: str,
        interests: str,
        travelers: int,
        hotels: List[Dict[str, Any]],
        restaurants: List[Dict[str, Any]],
        attractions: List[Dict[str, Any]],
        weather: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assembles a logical itinerary programmatically in Python using structured input lists.
        """
        # Parse start date
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        except Exception:
            start_date = datetime.now() + timedelta(days=1)

        # Select baseline hotel
        selected_hotel = hotels[0] if hotels else None
        hotel_lat = selected_hotel.get("latitude") if selected_hotel else None
        hotel_lng = selected_hotel.get("longitude") if selected_hotel else None

        # Categorize restaurants
        breakfast_spots = []
        lunch_dinner_spots = []
        
        for r in restaurants:
            name_lower = r.get("name", "").lower()
            cuisine_lower = r.get("cuisine", "").lower()
            is_breakfast = (
                r.get("serves_breakfast") or
                any(kw in name_lower or kw in cuisine_lower for kw in ["breakfast", "cafe", "bakery", "idli", "dosa", "coffee"])
            )
            if is_breakfast:
                breakfast_spots.append(r)
            else:
                lunch_dinner_spots.append(r)

        # Fallbacks if list is empty after categorization - use general restaurant list
        if not breakfast_spots:
            breakfast_spots = restaurants if restaurants else []
        if not lunch_dinner_spots:
            lunch_dinner_spots = restaurants if restaurants else []

        # Check weather conditions
        weather_main = weather.get("main", "Clear").lower()
        is_raining = any(kw in weather_main for kw in ["rain", "thunderstorm", "drizzle", "storm"])

        # Prioritize and rank attractions based on interests
        ranked_attractions = []
        interest_list = [i.strip().lower() for i in interests.split(",")] if interests and interests.lower() != "none" else []
        
        for a in attractions:
            score = a.get("rating", 4.0)
            # Boost score if attraction matches interests
            name_lower = a.get("name", "").lower()
            desc_lower = a.get("editorial", "").lower()
            types = [t.lower() for t in a.get("types", [])]
            
            for interest in interest_list:
                if interest in name_lower or interest in desc_lower or interest in types:
                    score += 1.0  # Interest match boost
            
            # Weather filter: penalize outdoor places if raining
            is_outdoor = any(t in types for t in ["park", "natural_feature", "beach", "waterfall", "garden", "zoo", "amusement_park"])
            if is_raining and is_outdoor:
                score -= 2.0  # Heavy rain penalty for outdoor attractions

            ranked_attractions.append((score, a))

        # Sort attractions descending by score
        ranked_attractions.sort(key=lambda x: x[0], reverse=True)
        sorted_attractions = [item[1] for item in ranked_attractions]

        # Programmatic scheduling loop
        itinerary_days = []
        attraction_idx = 0
        restaurant_rot_idx = 0
        breakfast_rot_idx = 0

        for d in range(1, days + 1):
            day_date = (start_date + timedelta(days=d-1)).strftime("%Y-%m-%d")
            day_activities = []
            
            # Daily checkpoints for coordinate routing
            current_lat = hotel_lat
            current_lng = hotel_lng
            last_location_name = selected_hotel.get("name") if selected_hotel else "Start"

            # Helper to create structured activity dict
            def add_activity(slot_type: str, title: str, category: str, location: str, start_time: str, end_time: str, notes: str, entity_id: str, lat: Optional[float], lng: Optional[float], cost: float = 0.0):
                nonlocal current_lat, current_lng, last_location_name
                # Calculate travel from last point
                dist = calculate_haversine(current_lat, current_lng, lat, lng)
                trav_time, transport_mode = estimate_travel(dist)
                
                # Update current position
                if lat is not None and lng is not None:
                    current_lat = lat
                    current_lng = lng
                    last_location_name = title

                day_activities.append({
                    "activity_id": f"act-{d}-{slot_type.lower()}-{len(day_activities)}",
                    "type": slot_type,
                    "title": title,
                    "category": category,
                    "location": location,
                    "latitude": lat,
                    "longitude": lng,
                    "start_datetime": f"{day_date}T{start_time}:00",
                    "end_datetime": f"{day_date}T{end_time}:00",
                    "start_time": start_time,
                    "end_time": end_time,
                    "travel_time": trav_time,
                    "transport": transport_mode,
                    "estimated_cost": 0.0,
                    "google_event_id": None,
                    "status": "pending",
                    f"{category.lower()}_id": entity_id,
                    "notes": notes
                })

            # --- 1. Breakfast (08:00 - 09:00) ---
            if breakfast_spots:
                b_spot = breakfast_spots[breakfast_rot_idx % len(breakfast_spots)]
                breakfast_rot_idx += 1
                add_activity(
                    slot_type="Breakfast",
                    title=b_spot.get("name"),
                    category="Food",
                    location=b_spot.get("address", "Local Eatery"),
                    start_time="08:00",
                    end_time="09:00",
                    notes="Start your day with local breakfast delicacies.",
                    entity_id=b_spot.get("restaurant_id"),
                    lat=b_spot.get("latitude"),
                    lng=b_spot.get("longitude"),
                    cost=0.0
                )

            # --- 2. Morning Attraction (09:30 - 12:00) ---
            if sorted_attractions:
                att = sorted_attractions[attraction_idx % len(sorted_attractions)]
                attraction_idx += 1
                weather_warning = " (Rain fallback indoor activity recommended)" if is_raining and any(t in att.get("types", []) for t in ["park", "beach", "waterfall"]) else ""
                add_activity(
                    slot_type="Sightseeing",
                    title=att.get("name"),
                    category="Sightseeing",
                    location=att.get("address", "Local Attraction"),
                    start_time="09:30",
                    end_time="12:00",
                    notes=f"{att.get('editorial', 'Popular local attraction.')}{weather_warning}",
                    entity_id=att.get("attraction_id"),
                    lat=att.get("latitude"),
                    lng=att.get("longitude"),
                    cost=0.0
                )

            # --- 3. Lunch (12:30 - 13:30) ---
            if lunch_dinner_spots:
                l_spot = lunch_dinner_spots[restaurant_rot_idx % len(lunch_dinner_spots)]
                restaurant_rot_idx += 1
                add_activity(
                    slot_type="Lunch",
                    title=l_spot.get("name"),
                    category="Food",
                    location=l_spot.get("address", "Lunch Diner"),
                    start_time="12:30",
                    end_time="13:30",
                    notes="Enjoy a traditional regional lunch.",
                    entity_id=l_spot.get("restaurant_id"),
                    lat=l_spot.get("latitude"),
                    lng=l_spot.get("longitude"),
                    cost=0.0
                )

            # --- 4. Afternoon Attraction (14:00 - 16:30) ---
            if sorted_attractions:
                att = sorted_attractions[attraction_idx % len(sorted_attractions)]
                attraction_idx += 1
                weather_warning = " (Rain fallback indoor activity recommended)" if is_raining and any(t in att.get("types", []) for t in ["park", "beach", "waterfall"]) else ""
                add_activity(
                    slot_type="Sightseeing",
                    title=att.get("name"),
                    category="Sightseeing",
                    location=att.get("address", "Sightseeing Spot"),
                    start_time="14:00",
                    end_time="16:30",
                    notes=f"{att.get('editorial', 'Fascinating cultural heritage spot.')}{weather_warning}",
                    entity_id=att.get("attraction_id"),
                    lat=att.get("latitude"),
                    lng=att.get("longitude"),
                    cost=0.0
                )

            # --- 5. Evening Activity (17:00 - 18:30) ---
            # Try to assign a viewpoint, market or shopping spot
            ev_att = None
            if sorted_attractions:
                # Find an evening-appropriate place (e.g. shopping, market, beach, point of interest)
                for candidate in sorted_attractions[attraction_idx:attraction_idx+5]:
                    c_types = [t.lower() for t in candidate.get("types", [])]
                    if any(t in c_types for t in ["shopping_mall", "store", "point_of_interest", "market", "beach"]):
                        ev_att = candidate
                        break
                if not ev_att:
                    ev_att = sorted_attractions[attraction_idx % len(sorted_attractions)]
                    attraction_idx += 1
            
            if ev_att:
                add_activity(
                    slot_type="Sightseeing",
                    title=ev_att.get("name"),
                    category="Sightseeing",
                    location=ev_att.get("address", "Evening Spot"),
                    start_time="17:00",
                    end_time="18:30",
                    notes=f"{ev_att.get('editorial', 'Perfect evening walk to relax or shop.')}",
                    entity_id=ev_att.get("attraction_id"),
                    lat=ev_att.get("latitude"),
                    lng=ev_att.get("longitude"),
                    cost=0.0
                )

            # --- 6. Dinner (19:00 - 20:30) ---
            if lunch_dinner_spots:
                d_spot = lunch_dinner_spots[restaurant_rot_idx % len(lunch_dinner_spots)]
                restaurant_rot_idx += 1
                add_activity(
                    slot_type="Dinner",
                    title=d_spot.get("name"),
                    category="Food",
                    location=d_spot.get("address", "Dinner Spot"),
                    start_time="19:00",
                    end_time="20:30",
                    notes="Unwind and enjoy a relaxing multi-course dinner.",
                    entity_id=d_spot.get("restaurant_id"),
                    lat=d_spot.get("latitude"),
                    lng=d_spot.get("longitude"),
                    cost=0.0
                )

            # --- 7. Hotel (21:00 - 08:00) ---
            if selected_hotel:
                add_activity(
                    slot_type="Hotel",
                    title=selected_hotel.get("name"),
                    category="Hotel",
                    location=selected_hotel.get("address", "Hotel Stay"),
                    start_time="21:00",
                    end_time="08:00",
                    notes="Check in and overnight stay.",
                    entity_id=selected_hotel.get("hotel_id"),
                    lat=selected_hotel.get("latitude"),
                    lng=selected_hotel.get("longitude"),
                    cost=0.0
                )

            itinerary_days.append({
                "day": d,
                "date": day_date,
                "activities": day_activities
            })

        return {
            "city": city.title(),
            "days": itinerary_days
        }
