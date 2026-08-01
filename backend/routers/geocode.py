// backend/routers/geocode.py
import os
from fastapi import APIRouter, HTTPException
from ..services.geocode_service import geocode_address, reverse_geocode
from pydantic import BaseModel

router = APIRouter()

class GeocodeResponse(BaseModel):
    lat: float
    lon: float
    display_name: str | None = None
    address: str | None = None

@router.get("/api/geocode", response_model=GeocodeResponse)
async def geocode_endpoint(address: str):
    """Forward geocode an address using Nominatim."""
    try:
        result = await geocode_address(address)
        return GeocodeResponse(lat=result["lat"], lon=result["lon"], display_name=result.get("display_name"))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/api/reverse_geocode", response_model=GeocodeResponse)
async def reverse_geocode_endpoint(lat: float, lon: float):
    """Reverse geocode coordinates to a human readable address."""
    try:
        result = await reverse_geocode(lat, lon)
        return GeocodeResponse(lat=lat, lon=lon, address=result.get("address"))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
