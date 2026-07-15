import os
import re
from urllib.parse import quote

import requests
from fastapi import APIRouter, HTTPException, Query, Response


router = APIRouter()

_PHOTO_NAME = re.compile(r"^places/[^/]+/photos/[^/]+$")


@router.get("/place-photo")
def place_photo(
    photo_name: str = Query(...),
    maxwidth: int = Query(800, ge=1, le=4800),
) -> Response:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GOOGLE_PLACES_API_KEY is not configured",
        )

    if not _PHOTO_NAME.fullmatch(photo_name):
        raise HTTPException(status_code=400, detail="Invalid Google photo name")

    media_url = (
        "https://places.googleapis.com/v1/"
        f"{quote(photo_name, safe='/')}/media"
    )

    try:
        google_response = requests.get(
            media_url,
            params={
                "key": api_key,
                "maxWidthPx": maxwidth,
            },
            timeout=20,
            allow_redirects=True,
        )
        google_response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Google Places photo could not be loaded",
        ) from exc

    return Response(
        content=google_response.content,
        media_type=google_response.headers.get(
            "content-type",
            "image/jpeg",
        ),
        headers={"Cache-Control": "public, max-age=86400"},
    )
