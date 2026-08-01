from fastapi import APIRouter, HTTPException, Query
from ..services.route_service import get_route

router = APIRouter()

@router.get("/api/route", summary="Get driving route between two points")
async def get_route_endpoint(
    origin: str = Query(..., description="Origin as 'lat,lon'"),
    destination: str = Query(..., description="Destination as 'lat,lon'")
):
    """Return a route between two coordinates.

    The `origin` and `destination` query parameters are strings formatted as
    ``lat,lon``. The endpoint parses them, calls the internal ``get_route``
    service and returns the OSRM result.
    """
    try:
        ox, oy = map(float, origin.split(","))
        dx, dy = map(float, destination.split(","))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid coordinate format; expected 'lat,lon'.")
    try:
        return await get_route((ox, oy), (dx, dy))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
