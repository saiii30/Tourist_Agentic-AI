from fastapi import APIRouter

from ..AI.services.osrm_service import geocode_place, optimize_route_osrm

router = APIRouter()

@router.post("/optimize-route")
async def optimize_route(data: dict):
    """Return optimized trip stops in the shape consumed by the planner map."""
    hotel_name = data.get("hotelName") or "Hotel Stay"
    city_name = data.get("cityName") or ""
    default_lat, default_lng = geocode_place(city_name, city_name) if city_name else (20.5937, 78.9629)
    hotel_lat = float(data.get("hotelLat") or default_lat)
    hotel_lng = float(data.get("hotelLng") or default_lng)
    places = data.get("places") or []
    start_location = data.get("startLocation")
    start_coords = None
    if data.get("startLat") is not None and data.get("startLng") is not None:
        start_coords = (float(data.get("startLat")), float(data.get("startLng")))

    return optimize_route_osrm(
        hotel_name=hotel_name,
        hotel_coords=(hotel_lat, hotel_lng),
        places=places,
        city_name=city_name,
        start_location=start_location,
        start_coords=start_coords,
    )
