# backend/AI/rag/schemas.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class CollectionType(str, Enum):
    ATTRACTIONS = "tourism_attractions"
    HERITAGE = "tourism_heritage"
    HOTELS = "tourism_hotels"
    RESTAURANTS = "tourism_restaurants"
    FESTIVALS = "tourism_festivals"
    WILDLIFE = "tourism_wildlife"
    TRANSPORT = "tourism_transport"
    EMERGENCY = "tourism_emergency"
    CUSTOMS = "tourism_customs"
    TREKKING = "tourism_trekking"
    WEATHER = "tourism_weather"
    ADVISORIES = "tourism_advisories"

class SourceTrustLevel(int, Enum):
    GOVERNMENT = 100
    UNESCO = 100
    FOREST_DEPT = 98
    BOOKING_PARTNER = 90
    GENERAL_WIKI = 70

class ChunkMetadata(BaseModel):
    chunk_id: str
    country: str = "India"
    state: str = "Tamil Nadu"
    city: str
    destination: str
    category: str
    source_domain: str
    source_url: str
    last_updated: Optional[str] = None
    language: str = "en"

    # Operational extended fields
    season: Optional[str] = "All Year"
    family_friendly: bool = True
    wheelchair_access: bool = True
    pet_friendly: bool = False
    booking_required: bool = False
    avg_visit_duration_mins: int = 120
    best_visit_time: Optional[str] = "Morning"

    # Trust Scoring
    source_priority: str = "Government"
    trust_score: int = 100
    confidence: float = 0.95

class DocumentChunk(BaseModel):
    chunk_id: str
    content: str
    metadata: ChunkMetadata

class RoutePlan(BaseModel):
    collections: List[CollectionType]
    metadata_filters: Dict[str, Any] = Field(default_factory=dict)
    top_k: int = 5
    sub_queries: List[str] = Field(default_factory=list)

class RAGSearchResult(BaseModel):
    chunk_id: str
    content: str
    destination: str
    city: str
    category: str
    source_url: str
    source_domain: str
    trust_score: int
    relevance_score: float
    metadata: Dict[str, Any]
