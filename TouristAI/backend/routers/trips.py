import json
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy import text

from ..db import SessionLocal

router = APIRouter()

class TripCreate(BaseModel):
    name: str
    description: str | None = None
    waypoints: List[dict]  # [{'lat': float, 'lng': float}, ...]

class TripResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    waypoints: List[dict]

@router.post("/trips", response_model=TripResponse)
async def create_trip(trip: TripCreate):
    trip_id = str(uuid.uuid4())
    with SessionLocal() as db:
        db.execute(
            text("INSERT INTO trips (id, name, description, waypoints) VALUES (:id, :name, :description, :waypoints)"),
            {
                "id": trip_id,
                "name": trip.name,
                "description": trip.description,
                "waypoints": json.dumps(trip.waypoints),
            },
        )
        db.commit()
    return {"id": trip_id, "name": trip.name, "description": trip.description, "waypoints": trip.waypoints}

@router.get("/trips/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str):
    with SessionLocal() as db:
        row = db.execute(text("SELECT * FROM trips WHERE id = :id"), {"id": trip_id}).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Trip not found")
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "waypoints": json.loads(row["waypoints"]),
        }

@router.get("/trips", response_model=List[TripResponse])
async def list_trips():
    with SessionLocal() as db:
        rows = db.execute(text("SELECT * FROM trips")).fetchall()
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "description": r["description"],
                "waypoints": json.loads(r["waypoints"]),
            }
            for r in rows
        ]

@router.delete("/trips/{trip_id}")
async def delete_trip(trip_id: str):
    with SessionLocal() as db:
        result = db.execute(text("DELETE FROM trips WHERE id = :id"), {"id": trip_id})
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Trip not found")
    return {"status": "deleted"}
