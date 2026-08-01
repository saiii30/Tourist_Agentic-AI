from fastapi import APIRouter
import sys
import os

from backend.AI.app import ChatRequest, chat, chat_stream_response, CrowdPredictionRequest, predict_crowd_endpoint

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    return chat(req)

@router.post("/chat/stream")
async def chat_stream_endpoint(req: ChatRequest):
    return await chat_stream_response(req)

@router.post("/predict-crowd")
async def predict_crowd_api(req: CrowdPredictionRequest):
    return await predict_crowd_endpoint(req)
