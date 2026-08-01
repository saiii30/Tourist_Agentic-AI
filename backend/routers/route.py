// backend/routers/route.py
import os
from fastapi import APIRouter, HTTPException, Depends
from typing import Tuple
from pydantic import BaseModel

from ..services.route_service import get_route
from ..schemas.route import RouteResponse
from ..core.database import get_db  # placeholder if needed

router = APIRouter()

@router.get("/api/route", response_model=RouteResponse)
async def route_endpoint(origin: str, destination: str):
    """Accept `origin` and `destination` as `lat,lng` strings, return OSRM route.
    Example: /api/route?origin=9.9697,77.4768&destination=12.4244,75.7382
    """
    try:
        ox, oy = map(float, origin.split(","))
        dx, dy = map(float, destination.split(","))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid coordinate format")
    try:
        result = await get_route((ox, oy), (dx, dy))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return RouteResponse(**result)
