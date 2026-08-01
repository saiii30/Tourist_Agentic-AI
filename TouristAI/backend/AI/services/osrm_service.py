import requests
import urllib.parse
import hashlib
import random
from typing import Dict, List, Tuple, Any, Optional

OSRM_HOST = "https://router.project-osrm.org"
NOMINATIM_HOST = "https://nominatim.openstreetmap.org"

# Simple memory cache for geocoding
GEO_CACHE: Dict[str, Tuple[float, float]] = {}

def geocode_place(place_name: str, city_name: str) -> Tuple[float, float]:
    """
    Geocodes a place name + city name with fast deterministic hash offset.
    """
    place_clean = place_name.strip()
    city_clean = city_name.strip().lower()
    
    cache_key = f"{place_clean.lower()}|{city_clean}"
    if cache_key in GEO_CACHE:
        return GEO_CACHE[cache_key]
        
    fallbacks = {
        "trichy": (10.7905, 78.7047),
        "tiruchirappalli": (10.7905, 78.7047),
        "coorg": (12.4244, 75.7382),
        "madikeri": (12.4244, 75.7382),
        "theni": (10.0104, 77.4768),
        "munnar": (10.0889, 77.0595),
        "dindigul": (10.3673, 77.9803),
        "dindugal": (10.3673, 77.9803),
        "goa": (15.2993, 74.1240),
        "hampi": (15.3350, 76.4600),
        "mysore": (12.2958, 76.6394),
        "madurai": (9.9252, 78.1198),
        "coimbatore": (11.0168, 76.9558),
        "ooty": (11.4102, 76.6950),
        "kodaikanal": (10.2381, 77.4892),
        "chennai": (13.0827, 80.2707),
        "bangalore": (12.9716, 77.5946),
        "bengaluru": (12.9716, 77.5946)
    }
    
    base_coords = fallbacks.get(city_clean, (13.0827, 80.2707))
    h = int(hashlib.md5(cache_key.encode()).hexdigest()[:6], 16)
    lat_offset = ((h % 100) - 50) * 0.0002
    lng_offset = (((h // 100) % 100) - 50) * 0.0002
    
    coords = (round(base_coords[0] + lat_offset, 6), round(base_coords[1] + lng_offset, 6))
    GEO_CACHE[cache_key] = coords
    return coords
        
    # Get/compute city center lat/lng
    city_key = f"city|{city_clean.lower()}"
    city_lat_lng = GEO_CACHE.get(city_key)
    
    if not city_lat_lng:
        try:
            headers = {"User-Agent": "TouristAI-Route-Optimizer/1.0 (sureka.dev@gmail.com)"}
            url = f"{NOMINATIM_HOST}/search?q={urllib.parse.quote(city_clean)}&format=json&limit=1"
            res = requests.get(url, headers=headers, timeout=2.5)
            if res.status_code == 200 and res.json():
                data = res.json()[0]
                city_lat_lng = (float(data["lat"]), float(data["lon"]))
                GEO_CACHE[city_key] = city_lat_lng
        except Exception:
            pass
            
    if not city_lat_lng:
        # Static defaults for popular cities in the region
        fallbacks = {
            "trichy": (10.7905, 78.7047),
            "tiruchirappalli": (10.7905, 78.7047),
            "coorg": (12.4244, 75.7382),
            "madikeri": (12.4244, 75.7382),
            "theni": (10.0104, 77.4768),
            "munnar": (10.0889, 77.0595),
            "dindigul": (10.3673, 77.9803),
            "dindugal": (10.3673, 77.9803),
            "goa": (15.2993, 74.1240),
            "hampi": (15.3350, 76.4600),
            "mysore": (12.2958, 76.6394),
            # Tamil Nadu
            "madurai": (9.9252, 78.1198),
            "coimbatore": (11.0168, 76.9558),
            "ooty": (11.4102, 76.6950),
            "kodaikanal": (10.2381, 77.4892),
            "pollachi": (10.6590, 77.0073),
            "palani": (10.4490, 77.5175),
            "batlagundu": (10.1666, 77.7509),
            "valparai": (10.3244, 76.9594),
            "tirunelveli": (8.7139, 77.7567),
            "kanyakumari": (8.0883, 77.5385),
            # Kerala
            "kumily": (9.6028, 77.1637),
            "thekkady": (9.5942, 77.1665),
            "kochi": (9.9312, 76.2673),
            "ernakulam": (9.9816, 76.2999),
            "thiruvananthapuram": (8.5241, 76.9366),
            "trivandrum": (8.5241, 76.9366),
            "thrissur": (10.5276, 76.2144),
            "kozhikode": (11.2588, 75.7804),
            "calicut": (11.2588, 75.7804),
            "alleppey": (9.4981, 76.3388),
            "alappuzha": (9.4981, 76.3388),
            "wayanad": (11.6854, 76.1320),
            # Karnataka
            "bangalore": (12.9716, 77.5946),
            "bengaluru": (12.9716, 77.5946),
            "hassan": (13.0068, 76.1003),
            "sakleshpur": (12.9467, 75.7839),
            "chikmagalur": (13.3161, 75.7720),
            "mangalore": (12.9141, 74.8560),
            "chennai": (13.0827, 80.2707),
            "mumbai": (19.0760, 72.8777),
            "delhi": (28.6139, 77.2090),
        }
        matched = None
        c_lower = city_clean.lower()
        for k, coords in fallbacks.items():
            if k in c_lower:
                matched = coords
                break
        city_lat_lng = matched or (10.3673, 77.9803)
        GEO_CACHE[city_key] = city_lat_lng

    if place_clean.lower() == city_clean.lower():
        GEO_CACHE[cache_key] = city_lat_lng
        return city_lat_lng

    # Deterministic coordinate offset using place name MD5 hash to keep markers stable
    hasher = hashlib.md5(place_clean.encode('utf-8'))
    seed = int(hasher.hexdigest(), 16)
    r = random.Random(seed)
    
    # 0.015 degree is roughly 1.6 km
    offset_lat = r.uniform(-0.012, 0.012)
    offset_lng = r.uniform(-0.012, 0.012)
    
    lat = city_lat_lng[0] + offset_lat
    lng = city_lat_lng[1] + offset_lng
    GEO_CACHE[cache_key] = (lat, lng)
    return (lat, lng)

def get_osrm_route(lat1: float, lng1: float, lat2: float, lng2: float) -> Tuple[float, float]:
    """
    Returns (distance_km, duration_minutes) between two points using OSRM,
    with a straight-line Haversine math fallback.
    """
    if lat1 == lat2 and lng1 == lng2:
        return 0.0, 0.0
        
    try:
        url = f"{OSRM_HOST}/route/v1/driving/{lng1},{lat1};{lng2},{lat2}"
        res = requests.get(url, params={"overview": "false", "steps": "false"}, timeout=2.0)
        if res.status_code == 200:
            data = res.json()
            if "routes" in data and data["routes"]:
                route = data["routes"][0]
                dist_km = route["distance"] / 1000.0
                dur_mins = route["duration"] / 60.0
                return dist_km, dur_mins
    except Exception as e:
        print(f"[OSRM] Route API error: {e}")
        
    # Haversine fallback
    import math
    try:
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lng2 - lng1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        dist_km = R * c
        # Coarse duration estimates (12 mins per km walking/slow, 3-4 mins for auto/car)
        if dist_km <= 1.0:
            dur_mins = dist_km * 12.0
        elif dist_km <= 5.0:
            dur_mins = dist_km * 4.0
        else:
            dur_mins = dist_km * 3.0
        return dist_km, dur_mins
    except Exception:
        return 0.0, 0.0

def optimize_route_osrm(
    hotel_name: str, 
    hotel_coords: Tuple[float, float], 
    places: List[Dict[str, Any]], 
    city_name: str,
    start_location: Optional[str] = None,
    start_coords: Optional[Tuple[float, float]] = None
) -> Dict[str, Any]:
    """
    Runs OSRM /trip optimization starting from the hotel, geocodes input places, 
    and returns the optimized order and route polylines, prepending the origin route if start_location is supplied.
    """
    start_info = None
    origin_to_hotel_polyline = []
    origin_distance_km = 0.0
    
    if start_coords or (start_location and start_location.lower() != "none"):
        try:
            if start_coords:
                slat, slng = start_coords
            else:
                slat, slng = geocode_place(start_location, start_location)
            start_info = {"name": start_location or "Current Location", "lat": slat, "lng": slng}
            
            # Fetch route from start_location to hotel
            route_url = f"{OSRM_HOST}/route/v1/driving/{slng},{slat};{hotel_coords[1]},{hotel_coords[0]}"
            route_res = requests.get(route_url, params={"overview": "full", "geometries": "geojson"}, timeout=2.0)
            if route_res.status_code == 200:
                r_data = route_res.json()
                if "routes" in r_data and r_data["routes"]:
                    r_route = r_data["routes"][0]
                    origin_distance_km = r_route.get("distance", 0.0) / 1000.0
                    r_geom = r_route.get("geometry", {})
                    r_coords = r_geom.get("coordinates", [])
                    origin_to_hotel_polyline = [[c[1], c[0]] for c in r_coords]
            else:
                # Fallback distance calculation using get_osrm_route
                dist_h, _ = get_osrm_route(slat, slng, hotel_coords[0], hotel_coords[1])
                origin_distance_km = dist_h
        except Exception as e:
            print(f"[OSRM] Origin routing error: {e}")

    # Geocode all activities/places
    geocoded_places = []
    coords_list = [f"{hotel_coords[1]},{hotel_coords[0]}"] # input 0: hotel [lng, lat]
    
    for i, p in enumerate(places):
        try:
            plat = float(p.get("lat") or p.get("latitude"))
            plng = float(p.get("lng") or p.get("longitude"))
        except (TypeError, ValueError):
            plat, plng = geocode_place(p["name"], city_name)
        coords_list.append(f"{plng},{plat}")
        geocoded_places.append({
            "name": p["name"],
            "lat": plat,
            "lng": plng,
            "original_index": i
        })
        
    # Call OSRM Trip API
    coordinate_string = ";".join(coords_list)
    url = f"{OSRM_HOST}/trip/v1/driving/{coordinate_string}"
    params = {
        "source": "first",
        "roundtrip": "false",
        "overview": "full",
        "geometries": "geojson",
        "steps": "false"
    }
    
    try:
        res = requests.get(url, params=params, timeout=3.5)
        if res.status_code == 200:
            data = res.json()
            if "trips" in data and data["trips"] and "waypoints" in data:
                trip = data["trips"][0]
                waypoints = data["waypoints"]
                
                # The OSRM waypoints array aligns to the input coords. 
                # waypoint_index indicates the sequence index in the optimized trip.
                visitation_order = [0] * len(coords_list)
                for input_idx, wp in enumerate(waypoints):
                    visit_seq = wp["waypoint_index"]
                    visitation_order[visit_seq] = input_idx
                
                # Reorder places according to visitation order (excluding hotel index 0 at start)
                ordered_places = []
                for visit_seq in range(1, len(visitation_order)):
                    input_idx = visitation_order[visit_seq]
                    if input_idx > 0: # Place index
                        ordered_places.append(geocoded_places[input_idx - 1])
                        
                # Extract polyline geometry
                geometry = trip.get("geometry", {})
                route_coordinates = geometry.get("coordinates", []) # list of [lng, lat]
                # Convert OSRM [lng, lat] to Leaflet-expected [lat, lng]
                leaflet_polyline = [[c[1], c[0]] for c in route_coordinates]
                
                if origin_to_hotel_polyline:
                    leaflet_polyline = origin_to_hotel_polyline + leaflet_polyline
                
                local_dist = trip.get("distance", 0.0) / 1000.0
                total_dist = origin_distance_km + local_dist

                return {
                    "success": True,
                    "hotel": {"name": hotel_name, "lat": hotel_coords[0], "lng": hotel_coords[1]},
                    "start": start_info,
                    "places": ordered_places,
                    "polyline": leaflet_polyline,
                    "distance_km": round(total_dist, 1),
                    "origin_distance_km": round(origin_distance_km, 1),
                    "local_distance_km": round(local_dist, 1),
                    "duration_mins": round((trip.get("duration", 0.0) / 60.0) + (origin_distance_km * 1.5), 1)
                }
    except Exception as e:
        print(f"[OSRM] Trip optimization API error: {e}")
        
    # Heuristic fallback if OSRM is down
    leaflet_polyline = []
    if start_info:
        leaflet_polyline.append([start_info["lat"], start_info["lng"]])
    leaflet_polyline.append([hotel_coords[0], hotel_coords[1]])
    for gp in geocoded_places:
        leaflet_polyline.append([gp["lat"], gp["lng"]])
        
    return {
        "success": False,
        "hotel": {"name": hotel_name, "lat": hotel_coords[0], "lng": hotel_coords[1]},
        "start": start_info,
        "places": geocoded_places,
        "polyline": leaflet_polyline,
        "distance_km": round(origin_distance_km + 20.0, 1),
        "origin_distance_km": round(origin_distance_km, 1),
        "local_distance_km": 20.0,
        "duration_mins": 0.0
    }
