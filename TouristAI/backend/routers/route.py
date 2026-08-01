from fastapi import APIRouter, Query
from typing import Dict
from ..services.route_service import RouteService

router = APIRouter()

@router.get("/route")
async def get_route(
    origin_lat: float = Query(..., description="Origin latitude"),
    origin_lng: float = Query(..., description="Origin longitude"),
    dest_lat: float = Query(..., description="Destination latitude"),
    dest_lng: float = Query(..., description="Destination longitude"),
    mode: str = Query("driving", enum=["driving", "walking", "cycling"], description="Routing profile"),
) -> Dict:
    """Return enriched route data from the routing provider.
    The response includes distance, duration, geometry, travel mode, summary, bbox, and placeholders for budget calculations.
    """
    origin = {"lat": origin_lat, "lng": origin_lng}
    destination = {"lat": dest_lat, "lng": dest_lng}
    route_info = await RouteService.get_route(origin, destination, mode)
    return route_info
