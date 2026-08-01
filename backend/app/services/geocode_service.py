import os
import logging
from typing import Tuple, Dict, Any
import httpx
from functools import lru_cache

logger = logging.getLogger(__name__)

NOMINATIM_BASE_URL = os.getenv("NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org")

@lru_cache(maxsize=128)
def _build_search_url(query: str) -> str:
    """Construct the Nominatim search URL.
    Returns JSON results, limited to 5 entries.
    """
    return f"{NOMINATIM_BASE_URL}/search?format=json&q={query}&limit=5"

@lru_cache(maxsize=128)
def _build_reverse_url(lat: float, lon: float) -> str:
    """Construct the Nominatim reverse geocode URL."""
    return f"{NOMINATIM_BASE_URL}/reverse?format=json&lat={lat}&lon={lon}"

async def geocode_address(address: str) -> Dict[str, Any]:
    """Geocode an address string via Nominatim.
    Returns the first result's latitude and longitude.
    """
    url = _build_search_url(address)
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers={"User-Agent": "TouristAI/1.0"})
        resp.raise_for_status()
        results = resp.json()
        if not results:
            raise ValueError(f"No geocoding result for '{address}'")
        first = results[0]
        return {"lat": float(first["lat"]), "lon": float(first["lon"]), "display_name": first.get("display_name")}

async def reverse_geocode(lat: float, lon: float) -> Dict[str, Any]:
    """Reverse geocode coordinates to a human readable address."""
    url = _build_reverse_url(lat, lon)
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers={"User-Agent": "TouristAI/1.0"})
        resp.raise_for_status()
        data = resp.json()
        return {"address": data.get("display_name"), "lat": lat, "lon": lon}
