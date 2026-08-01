import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _entity_id(item: Dict[str, Any]) -> str:
    return str(
        item.get("attraction_id")
        or item.get("restaurant_id")
        or item.get("hotel_id")
        or item.get("id")
        or item.get("name")
        or ""
    )


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
        weather: Dict[str, Any],
        current_location: str = "None",
        travel_mode: str = "None",
        diet: str = "None",
        transport_data: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assembles a logical itinerary programmatically in Python using structured input lists.
        """
        # Parse start date
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        except Exception:
            start_date = datetime.now() + timedelta(days=1)

        # Geocode entities if missing or carrying hardcoded fallback coordinates from another city
        from services.osrm_service import geocode_place
        city_lower = city.lower().strip()
        is_hyderabad = ("hyderabad" in city_lower)
        
        # Geocode hotels
        for h in hotels:
            lat = h.get("latitude") or h.get("lat")
            lng = h.get("longitude") or h.get("lng")
            if lat is None or lng is None or (not is_hyderabad and abs(_as_float(lat) - 17.385) < 0.2):
                plat, plng = geocode_place(h.get("name"), city)
                h["latitude"] = plat
                h["longitude"] = plng
            else:
                h["latitude"] = _as_float(lat)
                h["longitude"] = _as_float(lng)

        # Geocode restaurants
        for r in restaurants:
            lat = r.get("latitude") or r.get("lat")
            lng = r.get("longitude") or r.get("lng")
            if lat is None or lng is None or (not is_hyderabad and abs(_as_float(lat) - 17.441) < 0.2):
                plat, plng = geocode_place(r.get("name"), city)
                r["latitude"] = plat
                r["longitude"] = plng
            else:
                r["latitude"] = _as_float(lat)
                r["longitude"] = _as_float(lng)

        # Geocode attractions
        for a in attractions:
            lat = a.get("latitude") or a.get("lat")
            lng = a.get("longitude") or a.get("lng")
            if lat is None or lng is None or (not is_hyderabad and abs(_as_float(lat) - 17.383) < 0.2):
                plat, plng = geocode_place(a.get("name"), city)
                a["latitude"] = plat
                a["longitude"] = plng
            else:
                a["latitude"] = _as_float(lat)
                a["longitude"] = _as_float(lng)

        # Select baseline hotel
        budget_lower = (budget or "").lower()

        def hotel_score(hotel: Dict[str, Any]) -> float:
            rating = _as_float(hotel.get("rating"), 4.0)
            reviews = _as_float(hotel.get("reviews"), 0.0)
            price = _as_float(hotel.get("pricePerNight"), 0.0)
            score = rating * 3.0 + min(reviews, 5000) / 1000.0
            if price:
                if any(k in budget_lower for k in ["low", "budget", "cheap", "below", "under"]):
                    score -= price / 1500.0
                elif "moderate" in budget_lower:
                    score -= abs(price - 4000.0) / 2500.0
                elif "luxury" in budget_lower:
                    score += min(price, 12000.0) / 6000.0
            return score

        selected_hotel = max(hotels, key=hotel_score) if hotels else None
        hotel_lat = selected_hotel.get("latitude") if selected_hotel else None
        hotel_lng = selected_hotel.get("longitude") if selected_hotel else None

        # Filter restaurants by diet preference
        diet_lower = (diet or "").lower()
        if "vegetarian" in diet_lower and "non-vegetarian" not in diet_lower:
            veg_spots = [r for r in restaurants if r.get("serves_vegetarian") or "veg" in r.get("name", "").lower() or "vegetarian" in r.get("cuisine", "").lower()]
            if veg_spots:
                restaurants = veg_spots

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
            score = _as_float(a.get("rating"), 4.0)
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
        attraction_scores = {_entity_id(item[1]): item[0] for item in ranked_attractions}
        sorted_attractions = [item[1] for item in ranked_attractions]

        # Programmatic scheduling loop
        itinerary_days = []
        used_attraction_ids = set()
        restaurant_rot_idx = 0
        breakfast_rot_idx = 0

        has_travel = (current_location and current_location.lower() != "none")
        if has_travel and (not travel_mode or travel_mode.lower() == "none"):
            travel_mode = "Car"

        # Geocode starting location
        start_lat, start_lng = None, None
        if has_travel:
            try:
                start_lat, start_lng = geocode_place(current_location, current_location)
            except Exception as e:
                print(f"[OSRM] Origin geocoding failed: {e}")

        for d in range(1, days + 1):
            day_date = (start_date + timedelta(days=d-1)).strftime("%Y-%m-%d")
            day_activities = []
            
            # Daily checkpoints for coordinate routing
            current_lat = hotel_lat
            current_lng = hotel_lng
            
            if has_travel and d == 1 and start_lat is not None and start_lng is not None:
                current_lat = start_lat
                current_lng = start_lng
                
            last_location_name = selected_hotel.get("name") if selected_hotel else "Start"

            # Helper to create structured activity dict
            def add_activity(slot_type: str, title: str, category: str, location: str, start_time: str, end_time: str, notes: str, entity_id: str, lat: Optional[float], lng: Optional[float], cost: float = 0.0):
                nonlocal current_lat, current_lng, last_location_name

                def find_google_photo_name() -> Optional[str]:
                    source_list: List[Dict[str, Any]] = []
                    id_keys: List[str] = []
                    if category == "Hotel":
                        source_list = hotels or []
                        id_keys = ["hotel_id", "id"]
                    elif category == "Food":
                        source_list = restaurants or []
                        id_keys = ["restaurant_id", "id"]
                    else:
                        source_list = attractions or []
                        id_keys = ["attraction_id", "id"]

                    for item in source_list:
                        if entity_id and any(str(item.get(key)) == str(entity_id) for key in id_keys):
                            return item.get("googlePhotoName") or item.get("photo_reference")
                        if title and str(item.get("name", "")).strip().lower() == str(title).strip().lower():
                            return item.get("googlePhotoName") or item.get("photo_reference")
                    return None
                
                def clean_time_str(t_str: str) -> str:
                    if not t_str:
                        return "09:00"
                    t_str = t_str.strip()
                    try:
                        for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M"):
                            t_norm = t_str.replace('\u202f', ' ').replace(' ', ' ')
                            try:
                                from datetime import datetime as dt_class
                                dt = dt_class.strptime(t_norm, fmt)
                                return dt.strftime("%H:%M")
                            except:
                                pass
                        
                        parts = re.split(r'[:\s]', t_str)
                        h = int(parts[0]) % 24
                        m = int(parts[1][:2]) % 60
                        return f"{h:02d}:{m:02d}"
                    except Exception:
                        return "09:00"

                start_time = clean_time_str(start_time)
                end_time = clean_time_str(end_time)

                # Calculate travel from last point using OSRM
                from services.osrm_service import get_osrm_route
                dist = 0.0
                trav_mins = 0.0
                
                if current_lat is not None and current_lng is not None and lat is not None and lng is not None:
                    dist, trav_mins = get_osrm_route(current_lat, current_lng, lat, lng)
                    
                if dist == 0.0:
                    trav_time, transport_mode = "0 mins", "Stay"
                else:
                    if trav_mins < 1.0:
                        trav_time = "1 min"
                    else:
                        trav_time = f"{int(round(trav_mins))} mins"
                        
                    if dist <= 1.0:
                        transport_mode = "Walking"
                    elif dist <= 5.0:
                        transport_mode = "Auto Rickshaw"
                    else:
                        transport_mode = "Cab"
                
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
                    "distance": f"{dist:.1f} km" if dist else "0 km",
                    "estimated_cost": cost,
                    "google_event_id": None,
                    "status": "pending",
                    f"{category.lower()}_id": entity_id,
                    "googlePhotoName": find_google_photo_name(),
                    "notes": notes
                })

            def pick_attraction(prefer_evening: bool = False) -> Optional[Dict[str, Any]]:
                if not sorted_attractions:
                    return None

                candidates = []
                evening_types = {"shopping_mall", "store", "point_of_interest", "market", "beach"}
                for attraction in sorted_attractions:
                    attraction_id = _entity_id(attraction)
                    if attraction_id in used_attraction_ids:
                        continue

                    types = {str(t).lower() for t in attraction.get("types", [])}
                    base = attraction_scores.get(attraction_id, _as_float(attraction.get("rating"), 4.0))
                    dist = calculate_haversine(current_lat, current_lng, attraction.get("latitude"), attraction.get("longitude"))
                    distance_penalty = min(dist, 20.0) / 8.0 if dist else 0.0
                    evening_bonus = 1.0 if prefer_evening and types.intersection(evening_types) else 0.0
                    candidates.append((base + evening_bonus - distance_penalty, attraction))

                if not candidates:
                    used_attraction_ids.clear()
                    for attraction in sorted_attractions:
                        base = attraction_scores.get(_entity_id(attraction), _as_float(attraction.get("rating"), 4.0))
                        candidates.append((base, attraction))

                candidates.sort(key=lambda item: item[0], reverse=True)
                chosen = candidates[0][1]
                chosen_id = _entity_id(chosen)
                if chosen_id:
                    used_attraction_ids.add(chosen_id)
                return chosen

            if has_travel and d == 1:
                # Check for scraped ticket options
                best_ticket = None
                if transport_data:
                    # The service returns ranked/sorted tickets
                    best_ticket = transport_data[0]

                if best_ticket:
                    arrival_start = best_ticket.get("departure", "08:00")
                    arrival_end = best_ticket.get("arrival", "12:00")
                    travel_time_str = best_ticket.get("duration", "4h 00m")
                    t_mode = best_ticket.get("mode", "Transport")
                    cost = float(best_ticket.get("price", 0.0))
                    
                    # Compute check-in hour dynamically based on arrival
                    try:
                        arrival_hour = int(arrival_end.split(":")[0])
                        arrival_min = int(arrival_end.split(":")[1])
                    except Exception:
                        arrival_hour = 12
                        arrival_min = 0

                    add_activity(
                        slot_type="Transport",
                        title=f"Board [{t_mode}] {best_ticket.get('carrier')}",
                        category="Transport",
                        location=f"{current_location.title()} to {city.title()}",
                        start_time=arrival_start,
                        end_time=arrival_end,
                        notes=f"Scraped recommendation: {best_ticket.get('vehicle_type')} ticket. Booking Source: {best_ticket.get('booking_source')}. Rating: ⭐ {best_ticket.get('rating')}. [Book Ticket]({best_ticket.get('booking_url')})",
                        entity_id=best_ticket.get("id"),
                        lat=hotel_lat,
                        lng=hotel_lng,
                        cost=cost
                    )
                    
                    arrival_end_hour = arrival_hour
                    arrival_end_min = arrival_min
                else:
                    # --- 1. Arrival Travel (calculated via OSRM) ---
                    from services.osrm_service import get_osrm_route
                    travel_dist, travel_mins = 0.0, 0.0
                    if start_lat is not None and start_lng is not None and hotel_lat is not None and hotel_lng is not None:
                        travel_dist, travel_mins = get_osrm_route(start_lat, start_lng, hotel_lat, hotel_lng)
                    
                    # Calculate realistic start and end times based on travel duration
                    arrival_start = "08:00"
                    travel_hours = int(travel_mins // 60)
                    travel_remainder_mins = int(travel_mins % 60)
                    arrival_end_hour = 8 + travel_hours
                    arrival_end_min = travel_remainder_mins
                    if arrival_end_min >= 60:
                        arrival_end_hour += 1
                        arrival_end_min -= 60
                    arrival_end = f"{arrival_end_hour:02d}:{arrival_end_min:02d}"
                    
                    # Format travel time for display
                    if travel_mins < 60:
                        travel_time_str = f"{int(travel_mins)} mins"
                    else:
                        travel_time_str = f"{travel_hours}h {travel_remainder_mins}m"
                    
                    add_activity(
                        slot_type="Transport",
                        title=f"Travel from {current_location.title()} to {city.title()}",
                        category="Transport",
                        location=f"{current_location.title()} to {city.title()}",
                        start_time=arrival_start,
                        end_time=arrival_end,
                        notes=f"Board your preferred {travel_mode.title()} from {current_location.title()} to travel to {city.title()}. Distance: {travel_dist:.1f} km, Duration: {travel_time_str}",
                        entity_id=None,
                        lat=hotel_lat,
                        lng=hotel_lng
                    )
                
                # --- 2. Check in Hotel (dynamic timing based on arrival) ---
                if selected_hotel:
                    # Calculate check-in time 30 mins after arrival
                    checkin_hour = arrival_end_hour
                    checkin_min = arrival_end_min + 30
                    if checkin_min >= 60:
                        checkin_hour += 1
                        checkin_min -= 60
                    checkin_start = arrival_end
                    checkin_end = f"{checkin_hour:02d}:{checkin_min:02d}"
                    
                    add_activity(
                        slot_type="Hotel",
                        title=selected_hotel.get("name"),
                        category="Hotel",
                        location=selected_hotel.get("address", "Hotel Stay"),
                        start_time=checkin_start,
                        end_time=checkin_end,
                        notes="Check in and freshen up at the hotel.",
                        entity_id=selected_hotel.get("hotel_id"),
                        lat=selected_hotel.get("latitude"),
                        lng=selected_hotel.get("longitude")
                    )

                if checkin_hour >= 17:
                    dinner_end = checkin_end
                    if lunch_dinner_spots and checkin_hour < 22:
                        d_spot = lunch_dinner_spots[restaurant_rot_idx % len(lunch_dinner_spots)]
                        restaurant_rot_idx += 1
                        dinner_start = checkin_end
                        dinner_end_hour = checkin_hour + 1
                        dinner_end_min = checkin_min + 30
                        if dinner_end_min >= 60:
                            dinner_end_hour += 1
                            dinner_end_min -= 60
                        dinner_end = f"{dinner_end_hour:02d}:{dinner_end_min:02d}"

                        add_activity(
                            slot_type="Dinner",
                            title=d_spot.get("name"),
                            category="Food",
                            location=d_spot.get("address", "Dinner Spot"),
                            start_time=dinner_start,
                            end_time=dinner_end,
                            notes="Have a light dinner after arrival and check-in.",
                            entity_id=d_spot.get("restaurant_id"),
                            lat=d_spot.get("latitude"),
                            lng=d_spot.get("longitude")
                        )

                    if selected_hotel:
                        add_activity(
                            slot_type="Hotel",
                            title=selected_hotel.get("name"),
                            category="Hotel",
                            location=selected_hotel.get("address", "Hotel Stay"),
                            start_time=dinner_end,
                            end_time="08:00",
                            notes="Overnight stay.",
                            entity_id=selected_hotel.get("hotel_id"),
                            lat=selected_hotel.get("latitude"),
                            lng=selected_hotel.get("longitude")
                        )

                    itinerary_days.append({
                        "day": d,
                        "date": day_date,
                        "activities": day_activities
                    })
                    continue

                # --- 3. Lunch (dynamic timing based on check-in) ---
                lunch_end = "13:30"
                lunch_hour = 13
                lunch_min = 30
                if lunch_dinner_spots:
                    l_spot = lunch_dinner_spots[restaurant_rot_idx % len(lunch_dinner_spots)]
                    restaurant_rot_idx += 1
                    # Lunch starts 30 mins after check-in ends
                    lunch_start = checkin_end
                    lunch_hour = checkin_hour
                    lunch_min = checkin_min + 30
                    if lunch_min >= 60:
                        lunch_hour += 1
                        lunch_min -= 60
                    lunch_end = f"{lunch_hour:02d}:{lunch_min:02d}"
                    
                    add_activity(
                        slot_type="Lunch",
                        title=l_spot.get("name"),
                        category="Food",
                        location=l_spot.get("address", "Lunch Diner"),
                        start_time=lunch_start,
                        end_time=lunch_end,
                        notes="Enjoy a traditional regional lunch.",
                        entity_id=l_spot.get("restaurant_id"),
                        lat=l_spot.get("latitude"),
                        lng=l_spot.get("longitude")
                    )

                # --- 4. Afternoon Attraction (dynamic timing based on lunch) ---
                att = pick_attraction()
                if att:
                    weather_warning = " (Rain fallback indoor activity recommended)" if is_raining and any(t in att.get("types", []) for t in ["park", "beach", "waterfall"]) else ""
                    # Afternoon starts 30 mins after lunch ends
                    afternoon_start = lunch_end
                    afternoon_hour = lunch_hour
                    afternoon_min = lunch_min + 30
                    if afternoon_min >= 60:
                        afternoon_hour += 1
                        afternoon_min -= 60
                    afternoon_end_hour = afternoon_hour + 2
                    afternoon_end_min = afternoon_min + 30
                    if afternoon_end_min >= 60:
                        afternoon_end_hour += 1
                        afternoon_end_min -= 60
                    afternoon_end = f"{afternoon_end_hour:02d}:{afternoon_end_min:02d}"
                    
                    # Enrich notes with RAG ground-truth rules (dress code, entry fees, photography policy)
                    rag_extra = ""
                    try:
                        from rag.service import rag_service
                        r_res = rag_service.query_rag(att.get("name", ""), agent_name="ItineraryAgent", city=city, top_k=1)
                        if r_res.get("has_knowledge") and r_res.get("context_text"):
                            snip = r_res["context_text"].replace("\n", " ").strip()
                            if len(snip) > 150:
                                snip = snip[:150] + "..."
                            rag_extra = f" | 📜 Verified RAG Info: {snip}"
                    except Exception:
                        pass

                    add_activity(
                        slot_type="Sightseeing",
                        title=att.get("name"),
                        category="Sightseeing",
                        location=att.get("address", "Sightseeing Spot"),
                        start_time=afternoon_start,
                        end_time=afternoon_end,
                        notes=f"{att.get('editorial', 'Fascinating cultural heritage spot.')}{weather_warning}{rag_extra}",
                        entity_id=att.get("attraction_id"),
                        lat=att.get("latitude"),
                        lng=att.get("longitude")
                    )

                # --- 5. Evening Activity (dynamic timing based on afternoon) ---
                ev_att = pick_attraction(prefer_evening=True)
                if ev_att:
                    # Evening starts 30 mins after afternoon ends
                    evening_start = afternoon_end
                    evening_hour = afternoon_end_hour
                    evening_min = afternoon_end_min + 30
                    if evening_min >= 60:
                        evening_hour += 1
                        evening_min -= 60
                    evening_end_hour = evening_hour + 1
                    evening_end_min = evening_min + 30
                    if evening_end_min >= 60:
                        evening_end_hour += 1
                        evening_end_min -= 60
                    evening_end = f"{evening_end_hour:02d}:{evening_end_min:02d}"
                    
                    add_activity(
                        slot_type="Sightseeing",
                        title=ev_att.get("name"),
                        category="Sightseeing",
                        location=ev_att.get("address", "Evening Spot"),
                        start_time=evening_start,
                        end_time=evening_end,
                        notes=f"{ev_att.get('editorial', 'Perfect evening walk to relax or shop.')}",
                        entity_id=ev_att.get("attraction_id"),
                        lat=ev_att.get("latitude"),
                        lng=ev_att.get("longitude")
                    )

                # --- 6. Dinner (dynamic timing based on evening) ---
                if lunch_dinner_spots:
                    d_spot = lunch_dinner_spots[restaurant_rot_idx % len(lunch_dinner_spots)]
                    restaurant_rot_idx += 1
                    # Dinner starts 30 mins after evening ends
                    dinner_start = evening_end
                    dinner_hour = evening_end_hour
                    dinner_min = evening_end_min + 30
                    if dinner_min >= 60:
                        dinner_hour += 1
                        dinner_min -= 60
                    dinner_end_hour = dinner_hour + 1
                    dinner_end_min = dinner_min + 30
                    if dinner_end_min >= 60:
                        dinner_end_hour += 1
                        dinner_end_min -= 60
                    dinner_end = f"{dinner_end_hour:02d}:{dinner_end_min:02d}"
                    
                    add_activity(
                        slot_type="Dinner",
                        title=d_spot.get("name"),
                        category="Food",
                        location=d_spot.get("address", "Dinner Spot"),
                        start_time=dinner_start,
                        end_time=dinner_end,
                        notes="Unwind and enjoy a relaxing multi-course dinner.",
                        entity_id=d_spot.get("restaurant_id"),
                        lat=d_spot.get("latitude"),
                        lng=d_spot.get("longitude")
                    )

                # --- 7. Hotel Stay (dynamic timing based on dinner) ---
                if selected_hotel:
                    # Hotel stay starts 30 mins after dinner ends
                    hotel_start = dinner_end
                    hotel_end = "08:00"  # Next morning
                    
                    add_activity(
                        slot_type="Hotel",
                        title=selected_hotel.get("name"),
                        category="Hotel",
                        location=selected_hotel.get("address", "Hotel Stay"),
                        start_time=hotel_start,
                        end_time=hotel_end,
                        notes="Overnight stay.",
                        entity_id=selected_hotel.get("hotel_id"),
                        lat=selected_hotel.get("latitude"),
                        lng=selected_hotel.get("longitude")
                    )

            elif has_travel and d == days:
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
                        lng=b_spot.get("longitude")
                    )

                # --- 2. Morning Attraction (09:30 - 12:00) ---
                att = pick_attraction()
                if att:
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
                        lng=att.get("longitude")
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
                        lng=l_spot.get("longitude")
                    )

                # --- 4. Afternoon Attraction (dynamic timing based on lunch) ---
                att = pick_attraction()
                if att:
                    weather_warning = " (Rain fallback indoor activity recommended)" if is_raining and any(t in att.get("types", []) for t in ["park", "beach", "waterfall"]) else ""
                    # Afternoon starts 30 mins after lunch ends
                    afternoon_start = "13:30"
                    afternoon_end = "16:30"
                    
                    add_activity(
                        slot_type="Sightseeing",
                        title=att.get("name"),
                        category="Sightseeing",
                        location=att.get("address", "Sightseeing Spot"),
                        start_time=afternoon_start,
                        end_time=afternoon_end,
                        notes=f"{att.get('editorial', 'Fascinating cultural heritage spot.')}{weather_warning}",
                        entity_id=att.get("attraction_id"),
                        lat=att.get("latitude"),
                        lng=att.get("longitude")
                    )

                # --- 5. Return Travel ---
                best_ticket = None
                if transport_data:
                    # Use a different ticket for return if available, else first one
                    best_ticket = transport_data[1] if len(transport_data) > 1 else transport_data[0]

                if best_ticket:
                    return_start = "17:00"
                    return_end = "21:00"
                    t_mode = best_ticket.get("mode", "Transport")
                    cost = float(best_ticket.get("price", 0.0))
                    
                    add_activity(
                        slot_type="Transport",
                        title=f"Board return [{t_mode}] {best_ticket.get('carrier')}",
                        category="Transport",
                        location=f"{city.title()} to {current_location.title()}",
                        start_time=return_start,
                        end_time=return_end,
                        notes=f"Scraped return recommendation: {best_ticket.get('vehicle_type')} ticket. Booking Source: {best_ticket.get('booking_source')}. Rating: ⭐ {best_ticket.get('rating')}. [Book Ticket]({best_ticket.get('booking_url')})",
                        entity_id=best_ticket.get("id"),
                        lat=start_lat,
                        lng=start_lng,
                        cost=cost
                    )
                else:
                    from services.osrm_service import get_osrm_route
                    return_dist, return_mins = 0.0, 0.0
                    if hotel_lat is not None and hotel_lng is not None and start_lat is not None and start_lng is not None:
                        return_dist, return_mins = get_osrm_route(hotel_lat, hotel_lng, start_lat, start_lng)
                    
                    # Calculate realistic start and end times based on travel duration
                    return_start = afternoon_end  # Start return travel after afternoon attraction
                    return_hours = int(return_mins // 60)
                    return_remainder_mins = int(return_mins % 60)
                    return_start_hour = 16
                    return_start_min = 30
                    return_end_hour = return_start_hour + return_hours
                    return_end_min = return_start_min + return_remainder_mins
                    if return_end_min >= 60:
                        return_end_hour += 1
                        return_end_min -= 60
                    return_end = f"{return_end_hour:02d}:{return_end_min:02d}"
                    
                    # Format travel time for display
                    if return_mins < 60:
                        return_time_str = f"{int(return_mins)} mins"
                    else:
                        return_time_str = f"{return_hours}h {return_remainder_mins}m"
                    
                    add_activity(
                        slot_type="Transport",
                        title=f"Return Travel from {city.title()} to {current_location.title()}",
                        category="Transport",
                        location=f"{city.title()} to {current_location.title()}",
                        start_time=return_start,
                        end_time=return_end,
                        notes=f"Board your return {travel_mode.title()} from {city.title()} back to {current_location.title()}. Distance: {return_dist:.1f} km, Duration: {return_time_str}",
                        entity_id=None,
                        lat=start_lat,
                        lng=start_lng
                    )

            else:
                # --- Standard Day Plan ---
                # 1. Breakfast (08:00 - 09:00)
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
                        lng=b_spot.get("longitude")
                    )

                # 2. Morning Attraction (09:30 - 12:00)
                att = pick_attraction()
                if att:
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
                        lng=att.get("longitude")
                    )

                # 3. Lunch (12:30 - 13:30)
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
                        lng=l_spot.get("longitude")
                    )

                # 4. Afternoon Attraction (14:00 - 16:30)
                att = pick_attraction()
                if att:
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
                        lng=att.get("longitude")
                    )

                # 5. Evening Activity (17:00 - 18:30)
                ev_att = pick_attraction(prefer_evening=True)
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
                        lng=ev_att.get("longitude")
                    )

                # 6. Dinner (19:00 - 20:30)
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
                        lng=d_spot.get("longitude")
                    )

                # 7. Hotel Stay (21:00 - 08:00)
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
                        lng=selected_hotel.get("longitude")
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
