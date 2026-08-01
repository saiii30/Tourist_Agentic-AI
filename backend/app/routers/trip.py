import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.schemas.trip import TripCreateRequest, TripResponse
from app.models.orm import Trip
from app.core.database import get_db
from app.services.langgraph_supervisor import LangGraphSupervisor
import redis
import json

router = APIRouter()

# Redis client for WebSocket Pub/Sub
def get_redis():
    return redis.from_url("redis://localhost:6379/0")

@router.post("/", response_model=TripResponse)
async def create_trip(request: TripCreateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_trip = Trip(**request.dict())
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    supervisor = LangGraphSupervisor(str(db_trip.id))
    background_tasks.add_task(supervisor.run, request.dict())
    return TripResponse(trip_id=str(db_trip.id), status="queued")

@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str, db: Session = Depends(get_db)):
    db_trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not db_trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return TripResponse(trip_id=str(db_trip.id), status=db_trip.status, data={"itinerary": db_trip.itinerary})

@router.websocket("/ws/{trip_id}")
async def websocket_endpoint(websocket: WebSocket, trip_id: str):
    await websocket.accept()
    channel = f"trip:{trip_id}"
    r = get_redis()
    pubsub = r.pubsub()
    pubsub.subscribe(channel)
    try:
        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True, timeout=5.0)
            if message and isinstance(message["data"], bytes):
                await websocket.send_text(message["data"].decode())
    except WebSocketDisconnect:
        pass
    finally:
        pubsub.unsubscribe(channel)
