from fastapi import APIRouter, HTTPException, Query
from ..services.geocode_service import geocode_address, reverse_geocode

router = APIRouter()

@router.get("/api/geocode", summary="Geocode an address string")
async def geocode_endpoint(address: str = Query(..., description="Address to geocode")):
    """Return latitude and longitude for a given address using Nominatim."""
    try:
        return await geocode_address(address)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

@router.get("/api/reverse", summary="Reverse geocode coordinates to an address")
async def reverse_endpoint(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
):
    """Return a human‑readable address for the supplied coordinates."""
    try:
        return await reverse_geocode(lat, lon)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
