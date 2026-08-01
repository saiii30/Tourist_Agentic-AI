from pydantic import BaseModel
from typing import List, Dict, Any

class Geometry(BaseModel):
    type: str = "LineString"
    coordinates: List[List[float]]

class RouteResponse(BaseModel):
    geometry: Geometry
    distance: float
    duration: float
