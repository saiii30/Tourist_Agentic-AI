import json
import aiohttp
import sqlite3
import math
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional

router = APIRouter()

# Simple SQLite cache (creates DB file if missing)
DB_PATH = "nearby_cache.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS poi_cache (
            lat REAL,
            lng REAL,
            radius INTEGER,
            categories TEXT,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (lat, lng, radius, categories)
        )
        """
    )
    conn.commit()
    conn.close()

init_db()

CATEGORY_TAGS: Dict[str, List[tuple[str, str]]] = {
    "hospital": [("amenity", "hospital")],
    "pharmacy": [("amenity", "pharmacy")],
    "clinic": [("amenity", "clinic"), ("amenity", "doctors")],
    "police": [("amenity", "police")],
    "fire_station": [("amenity", "fire_station")],
    "emergency": [("amenity", "police"), ("amenity", "fire_station"), ("amenity", "hospital"), ("amenity", "pharmacy")],
    "shop": [("shop", "supermarket"), ("shop", "convenience"), ("shop", "mall"), ("shop", "department_store")],
    "supermarket": [("shop", "supermarket")],
    "atm": [("amenity", "atm"), ("amenity", "bank")],
    "fuel": [("amenity", "fuel")],
}

CATEGORY_LABELS = {
    "hospital": "Hospital",
    "pharmacy": "Pharmacy",
    "clinic": "Clinic / Doctor",
    "police": "Police",
    "fire_station": "Fire Station",
    "emergency": "Emergency",
    "shop": "Shop / Essentials",
    "supermarket": "Supermarket",
    "atm": "ATM / Bank",
    "fuel": "Fuel",
}


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_m = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def element_coord(el: Dict) -> tuple[float | None, float | None]:
    lat = el.get("lat") or (el.get("center") or {}).get("lat")
    lng = el.get("lon") or (el.get("center") or {}).get("lon")
    return lat, lng


def label_for_category(category: str, tags: Dict) -> str:
    amenity = tags.get("amenity")
    shop = tags.get("shop")
    if amenity == "hospital":
        return "Hospital & ER"
    if amenity == "pharmacy":
        return "Pharmacy"
    if amenity in {"clinic", "doctors"}:
        return "Clinic / Doctor"
    if amenity == "police":
        return "Police"
    if amenity == "fire_station":
        return "Fire Station"
    if amenity == "atm":
        return "ATM"
    if amenity == "bank":
        return "Bank"
    if amenity == "fuel":
        return "Fuel Station"
    if shop:
        return shop.replace("_", " ").title()
    return CATEGORY_LABELS.get(category, category.replace("_", " ").title())


async def fetch_overpass(lat: float, lng: float, radius: int, category: str) -> List[Dict]:
    category_key = category.lower()
    tag_pairs = CATEGORY_TAGS.get(category_key, [("amenity", category_key)])
    overpass_url = "https://overpass-api.de/api/interpreter"

    selectors = []
    for tag, value in tag_pairs:
        selectors.extend([
            f'node["{tag}"="{value}"](around:{radius},{lat},{lng});',
            f'way["{tag}"="{value}"](around:{radius},{lat},{lng});',
            f'relation["{tag}"="{value}"](around:{radius},{lat},{lng});',
        ])
    query = f"[out:json][timeout:25];({''.join(selectors)});out center tags 40;"

    async with aiohttp.ClientSession() as session:
        async with session.post(overpass_url, data={"data": query}) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=502, detail="Overpass API error")
            data = await resp.json()
            elements = data.get("elements", [])
            results = []
            for el in elements:
                poi_lat, poi_lng = element_coord(el)
                if poi_lat is None or poi_lng is None:
                    continue
                tags = el.get("tags", {})
                distance_m = haversine_m(lat, lng, float(poi_lat), float(poi_lng))
                if distance_m > radius:
                    continue
                name = tags.get("name") or label_for_category(category_key, tags)
                phone = tags.get("phone") or tags.get("contact:phone") or tags.get("emergency")
                address_bits = [
                    tags.get("addr:housenumber"),
                    tags.get("addr:street"),
                    tags.get("addr:suburb"),
                    tags.get("addr:city"),
                ]
                address = ", ".join([bit for bit in address_bits if bit]) or tags.get("addr:full") or "Address not listed"
                results.append({
                    "id": f"{el.get('type', 'poi')}-{el.get('id')}",
                    "lat": poi_lat,
                    "lon": poi_lng,
                    "category": category_key,
                    "category_label": label_for_category(category_key, tags),
                    "name": name,
                    "address": address,
                    "phone": phone,
                    "distance_m": round(distance_m),
                    "tags": tags,
                })
            return sorted(results, key=lambda item: item["distance_m"])

def get_cached(lat: float, lng: float, radius: int, categories_key: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT response FROM poi_cache WHERE lat=? AND lng=? AND radius=? AND categories=?",
        (lat, lng, radius, categories_key),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

def cache_response(lat: float, lng: float, radius: int, categories_key: str, data: List[Dict]):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO poi_cache (lat, lng, radius, categories, response) VALUES (?,?,?,?,?)",
        (lat, lng, radius, categories_key, json.dumps(data)),
    )
    conn.commit()
    conn.close()

@router.get("/nearby", response_model=List[Dict])
async def nearby(
    lat: float = Query(..., description="Latitude in decimal degrees"),
    lng: float = Query(..., description="Longitude in decimal degrees"),
    radius: int = Query(1000, ge=10, le=50000, description="Search radius in meters"),
    category: List[str] = Query(..., description="POI categories (multiple allowed)"),
    open_now: Optional[bool] = Query(None, description="Filter places that are currently open"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating (0‑5)"),
    max_price: Optional[int] = Query(None, ge=0, description="Maximum price level"),
):
    """Return points of interest around a coordinate.
    Supports multiple categories and optional filters.
    """
    # Build a cache key that concatenates categories sorted
    categories_key = ",".join(sorted(category))
    cached = get_cached(lat, lng, radius, categories_key)
    if cached is not None:
        return cached
    # Fetch each category sequentially (could be parallelized)
    results: List[Dict] = []
    for cat in category:
        results.extend(await fetch_overpass(lat, lng, radius, cat))
    # Simple placeholder filters – real implementations would need more data
    if open_now:
        results = [p for p in results if p["tags"].get("opening_hours")]
    if min_rating is not None:
        results = [p for p in results if float(p["tags"].get("rating", 0)) >= min_rating]
    if max_price is not None:
        results = [p for p in results if int(p["tags"].get("price_level", 0)) <= max_price]
    cache_response(lat, lng, radius, categories_key, results)
    return results
