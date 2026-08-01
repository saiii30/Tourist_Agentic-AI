import os
import httpx
import time
from typing import Dict, List

# OSRM base URL – can be overridden via .env
OSRM_URL = os.getenv("OSRM_URL", "http://router.project-osrm.org")

# Simple in‑memory cache (key → (timestamp, data))
CACHE_TTL = 7 * 24 * 60 * 60  # 7 days
_route_cache: Dict[str, tuple] = {}

class RouteService:
    """Abstraction layer for routing providers (OSRM by default)."""

    @staticmethod
    def _cache_key(origin: Dict[str, float], destination: Dict[str, float], mode: str) -> str:
        # Use underscores instead of dots to keep the key filename‑safe
        return f"{origin['lat']}_{origin['lng']}_{destination['lat']}_{destination['lng']}_{mode}".replace(".", "_")

    @staticmethod
    def _get_cached(key: str):
        entry = _route_cache.get(key)
        if entry:
            ts, data = entry
            if time.time() - ts < CACHE_TTL:
                return data
            # Expired – remove
            del _route_cache[key]
        return None

    @staticmethod
    def _set_cache(key: str, data: Dict):
        _route_cache[key] = (time.time(), data)

    @staticmethod
    async def _fetch(url: str) -> Dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def get_route(origin: Dict[str, float], destination: Dict[str, float], mode: str = "driving") -> Dict:
        """Return enriched route information between origin and destination.

        Parameters
        ----------
        origin: dict with keys ``lat`` and ``lng``
        destination: dict with keys ``lat`` and ``lng``
        mode: routing profile – ``driving``, ``walking`` or ``cycling``
        """
        cache_key = RouteService._cache_key(origin, destination, mode)
        cached = RouteService._get_cached(cache_key)
        if cached:
            return cached
        url = (
            f"{OSRM_URL}/route/v1/{mode}/"
            f"{origin['lng']},{origin['lat']};{destination['lng']},{destination['lat']}"
            "?overview=full&geometries=geojson&steps=false"
        )
        data = await RouteService._fetch(url)
        route = data.get("routes", [{}])[0]
        coords = route.get("geometry", {}).get("coordinates", [])
        # Compute bounding box
        if coords:
            lons, lats = zip(*coords)
            bbox = [min(lons), min(lats), max(lons), max(lats)]
        else:
            bbox = []
        result = {
            "distance_km": round(route.get("distance", 0) / 1000, 2),
            "duration_min": round(route.get("duration", 0) / 60, 1),
            "geometry": coords,
            "travel_mode": mode,
            "summary": route.get("summary", ""),
            "bbox": bbox,
            "fuel_estimate": None,  # Filled later by Budget Agent
            "estimated_cost": None,  # Filled later by Budget Agent
            "walking_time": round(route.get("distance", 0) / 1.4 / 60, 1) if route.get("distance") else None,
            "cycling_time": round(route.get("distance", 0) / 4.1 / 60, 1) if route.get("distance") else None,
        }
        RouteService._set_cache(cache_key, result)
        return result

    @staticmethod
    async def get_trip_route(stops: List[Dict[str, float]], mode: str = "driving") -> Dict:
        """Placeholder for future multi‑stop trip optimization using the OSRM *trip* service.
        Returns a single‑leg enriched route (first→last) for now.
        """
        if not stops or len(stops) < 2:
            return {}
        origin = stops[0]
        destination = stops[-1]
        return await RouteService.get_route(origin, destination, mode)

    @staticmethod
    def calculate_distance(coord1: Dict[str, float], coord2: Dict[str, float]) -> float:
        """Haversine distance in kilometres – useful for quick client‑side estimates."""
        from math import radians, cos, sin, asin, sqrt
        lat1, lon1 = radians(coord1["lat"]), radians(coord1["lng"])
        lat2, lon2 = radians(coord2["lat"]), radians(coord2["lng"])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return 6371 * c
