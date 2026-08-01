import os
import logging
from typing import Tuple, Dict, Any
import httpx
from functools import lru_cache

logger = logging.getLogger(__name__)

OSRM_BASE_URL = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org")

@lru_cache(maxsize=128)
def _build_route_url(origin: Tuple[float, float], destination: Tuple[float, float]) -> str:
    """Construct the OSRM route URL.
    Uses the `driving` profile and requests geometry in geojson format.
    """
    ox, oy = origin
    dx, dy = destination
    return f"{OSRM_BASE_URL}/route/v1/driving/{ox},{oy};{dx},{dy}?overview=full&geometries=geojson"

async def get_route(origin: Tuple[float, float], destination: Tuple[float, float]) -> Dict[str, Any]:
    """Fetch route from OSRM.
    Returns a dict with keys: `geometry` (GeoJSON LineString), `distance` (meters), `duration` (seconds).
    Raises ``httpx.HTTPError`` on network issues.
    """
    url = _build_route_url(origin, destination)
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        if not data.get("routes"):
            raise ValueError("No route found for given coordinates")
        route = data["routes"][0]
        result = {
            "geometry": route["geometry"],  # GeoJSON LineString
            "distance": route.get("distance"),
            "duration": route.get("duration"),
        }
        logger.debug("OSRM route fetched: %s", result)
        return result
