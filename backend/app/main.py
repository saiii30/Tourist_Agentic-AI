# FastAPI entrypoint for TouristAI

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import trip, route, geocode

app = FastAPI(
    title="TouristAI Trip Planner",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS: allow all origins for development (restrict in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trip.router, prefix="/api/trip")
app.include_router(route.router)
app.include_router(geocode.router)

# WebSocket placeholder – the router will register the endpoint

