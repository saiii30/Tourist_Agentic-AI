import os
import json
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
client = redis.from_url(REDIS_URL)

def publish(channel: str, payload: dict) -> None:
    client.publish(channel, json.dumps(payload))

def get(key: str):
    val = client.get(key)
    return json.loads(val) if val else None

def set(key: str, value: dict, ex: int | None = None) -> None:
    client.set(key, json.dumps(value), ex=ex)
