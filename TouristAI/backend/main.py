from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import nearby, trips, optimize, chat, route

app = FastAPI(title="TouristAI Backend", version="0.1.0")

# Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(nearby, prefix="/api")
app.include_router(route.router, prefix="/api")
app.include_router(trips.router)
app.include_router(optimize.router)
app.include_router(chat.router)

# Root health check
@app.get("/health")
async def health_check():
    return {"status": "ok"}
