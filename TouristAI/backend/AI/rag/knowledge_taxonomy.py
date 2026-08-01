# backend/AI/rag/knowledge_taxonomy.py
"""
Stable RAG knowledge taxonomy for TouristAI.

Use these categories for information that does not change often. Runtime chat
logic can route and format answers more reliably when every chunk carries one
of these knowledge_type values.
"""

KNOWLEDGE_TYPES = {
    "destination_guide": {
        "label": "Destination Guides",
        "examples": ["overview", "things to see", "best time to visit", "local highlights"],
    },
    "history": {
        "label": "History",
        "examples": ["monument history", "museum background", "heritage stories"],
    },
    "culture": {
        "label": "Culture",
        "examples": ["festivals", "art forms", "food culture", "local identity"],
    },
    "local_customs": {
        "label": "Local Customs",
        "examples": ["dress code", "temple etiquette", "photography rules", "behavior guidelines"],
    },
    "temple_information": {
        "label": "Temple Information",
        "examples": ["temple timings", "entry rules", "darshan details", "footwear rules"],
    },
    "trekking_routes": {
        "label": "Trekking Routes",
        "examples": ["trail route", "difficulty", "permits", "forest restrictions"],
    },
    "hidden_places": {
        "label": "Hidden Places",
        "examples": ["lesser-known attractions", "offbeat viewpoints", "local recommendations"],
    },
    "safety_tips": {
        "label": "Safety Tips",
        "examples": ["emergency numbers", "women safety", "weather warnings", "local cautions"],
    },
    "packing_guides": {
        "label": "Packing Guides",
        "examples": ["seasonal packing", "trek packing", "temple visit packing"],
    },
    "visa_information": {
        "label": "Visa Information",
        "examples": ["visa rules", "passport requirements", "entry documents"],
    },
    "state_tourism_documents": {
        "label": "State Tourism Documents",
        "examples": ["state brochures", "tourism department guides", "official circuits"],
    },
}

SOURCE_TYPES = {
    "official_tourism_website": 100,
    "government_brochure": 100,
    "state_tourism_document": 100,
    "unesco_information": 100,
    "pdf_brochure": 95,
    "tourism_board_pdf": 95,
    "curated_internal": 90,
}

CATEGORY_TO_KNOWLEDGE_TYPE = {
    "Heritage & Temple Customs": "local_customs",
    "Heritage & Culture": "history",
    "Official Government Tourism": "destination_guide",
    "Archaeological Heritage": "history",
    "Official Tourism Overview": "state_tourism_documents",
    "Official District Tourism": "destination_guide",
    "Museums & History": "history",
    "Emergency & Helplines": "safety_tips",
}


def normalize_knowledge_type(value: str | None, category: str | None = None) -> str:
    if value and value in KNOWLEDGE_TYPES:
        return value
    if category and category in CATEGORY_TO_KNOWLEDGE_TYPE:
        return CATEGORY_TO_KNOWLEDGE_TYPE[category]
    return "destination_guide"


def normalize_source_type(value: str | None) -> str:
    if value and value in SOURCE_TYPES:
        return value
    return "official_tourism_website"
