from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.AI.agents.concierge_agent import concierge_agent
from backend.AI.services.local_language_service import LANGUAGES, detect_language, phrasebook, translate


router = APIRouter()


class ConciergeRequest(BaseModel):
    question: str
    trip: Dict[str, Any] = Field(default_factory=dict)
    current_location: Optional[Any] = None


@router.post("/concierge")
async def concierge(req: ConciergeRequest):
    if not req.trip:
        return {
            "source": "concierge",
            "intent": "missing_trip",
            "answer": "Open or create a trip before using the AI Concierge.",
            "requires_confirmation": False,
        }
    return concierge_agent(req.question, req.trip, req.current_location)


class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    source_language: str = "en"
    target_language: str = "ta"


@router.get("/local-assist/languages")
async def local_assist_languages():
    return {"languages": [{"code": code, **details} for code, details in LANGUAGES.items()]}


@router.get("/local-assist/phrasebook")
async def local_assist_phrasebook(source_language: str = "en", target_language: str = "ta"):
    return {"phrases": phrasebook(source_language, target_language)}


@router.get("/local-assist/detect")
async def local_assist_detect(text: str):
    code = detect_language(text)
    return {"language": code, "name": LANGUAGES[code]["name"]}


@router.post("/local-assist/translate")
async def local_assist_translate(req: TranslationRequest):
    result = await translate(req.text, req.source_language, req.target_language)
    return {
        "source_language": req.source_language,
        "target_language": req.target_language,
        "original_text": req.text,
        **result,
    }
