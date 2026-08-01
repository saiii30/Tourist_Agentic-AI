"""Stable TouristAI app import.

The large FastAPI implementation lives in backend.AI.api.monolith. This file is
kept so existing imports such as backend.AI.app:app continue to work.
"""
from .api.monolith import *  # noqa: F401,F403
