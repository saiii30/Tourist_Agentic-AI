"""
ResponseBuilder for Discover Agent.

- Strict Wikipedia image lookup (no random/irrelevant fallback images).
- If a place has no valid Wikipedia photo, we simply omit the image
  (or fall back to the CITY's Wikipedia photo — never picsum/unsplash/people).
- Output format mirrors ChatGPT's "places near <city>" style:
    intro line -> hero image cards (side by side) -> numbered sections.
- No giant "Explore Around <City>" H1.
- Place names are clickable and open an inline Leaflet map on the frontend
  via a custom link scheme: `place://<name>|<city>|<lat>|<lon>`.
"""

import re
import urllib.parse
import requests

from services.crowd_service import predict_crowd
from services.nearby_services import NearbyService


UA = {"User-Agent": "TouristAI/1.0 (contact@example.com)"}
WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_REST = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# Wikipedia page types that are NEVER a real place
BAD_TYPES = {"disambiguation"}
BAD_DESC_KEYWORDS = (
    "actress", "actor", "singer", "politician", "cricketer", "film",
    "movie", "song", "album", "band", "author", "writer", "footballer",
    "player", "boxer", "wrestler", "businessman", "businesswoman",
    "novel", "book", "tv series", "television series",
)


def _wiki_page(query: str) -> dict | None:
    """Return the Wikipedia summary dict for the best-matching PLACE page, else None."""
    try:
        # 1) search
        r = requests.get(
            WIKI_API,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 5,
            },
            timeout=6,
            headers=UA,
        )
        hits = r.json().get("query", {}).get("search", [])
        if not hits:
            return None

        # 2) walk candidates until we find a real place page
        for hit in hits:
            title = hit["title"]
            s = requests.get(
                WIKI_REST + urllib.parse.quote(title),
                timeout=6,
                headers=UA,
            )
            if s.status_code != 200:
                continue
            data = s.json()

            if data.get("type") in BAD_TYPES:
                continue

            desc = (data.get("description") or "").lower()
            extract = (data.get("extract") or "").lower()

            # reject people / films / songs
            if any(k in desc for k in BAD_DESC_KEYWORDS):
                continue
            if desc.startswith(("indian ", "american ", "british ")) and any(
                k in desc for k in ("actor", "actress", "singer", "player")
            ):
                continue

            # must smell like a place
            place_hints = (
                "town", "city", "village", "beach", "waterfall", "temple",
                "fort", "hill", "mountain", "island", "district", "state",
                "region", "national park", "sanctuary", "monument", "lake",
                "river", "valley", "cave", "ghat", "palace", "museum",
                "market", "square", "peninsula",
            )
            if not (
                any(h in desc for h in place_hints)
                or any(h in extract[:400] for h in place_hints)
                or data.get("coordinates")
            ):
                continue

            return data
    except Exception:
        return None
    return None


def _wiki_image_and_page(query: str) -> tuple[str | None, str | None, tuple[float, float] | None]:
    """
    Return (image_url or None, wiki_page_url or None, (lat, lon) or None).
    NEVER returns a random image. If Wikipedia has no photo, image_url is None.
    """
    data = _wiki_page(query)
    if not data:
        return None, None, None
    img = (data.get("originalimage") or {}).get("source") or (
        data.get("thumbnail") or {}
    ).get("source")
    page = (data.get("content_urls") or {}).get("desktop", {}).get("page")
    coords = data.get("coordinates")
    latlon = (coords["lat"], coords["lon"]) if coords else None
    return img, page, latlon


def _place_media(name: str, city: str) -> tuple[str | None, str, tuple[float, float] | None]:
    """
    Return (image_url_or_None, link_url, latlon_or_None).
    link_url is Wikipedia if found, else Google Maps.
    image_url may be None (do NOT render an image in that case).
    """
    for q in (f"{name}, {city}", f"{name} {city}", name):
        img, page, latlon = _wiki_image_and_page(q)
        if img and page:
            return img, page, latlon
    maps_url = (
        "https://www.google.com/maps/search/?api=1&query="
        + urllib.parse.quote(f"{name}, {city}")
    )
    return None, maps_url, None


def _city_hero_image(city: str) -> str | None:
    """City-level Wikipedia photo used only as a shared banner if we want one."""
    img, _, _ = _wiki_image_and_page(city)
    return img


def _place_link(name: str, city: str, latlon: tuple[float, float] | None) -> str:
    """
    Custom scheme the React frontend intercepts to open an inline Leaflet map:
        place://<name>|<city>|<lat>|<lon>
    Falls back to just name|city if coords unknown (frontend can still geocode).
    """
    lat, lon = (latlon or ("", ""))
    payload = f"{name}|{city}|{lat}|{lon}"
    return "place://" + urllib.parse.quote(payload, safe="|")


# ---------------- main builder ----------------

class ResponseBuilder:

    @staticmethod
    def build(city: str, discover_result: dict) -> str:
        out: list[str] = []

        # 1. ChatGPT-style intro line (NO big H1 title)
        out.append(
            f"If you're looking for **places to visit near {city}** "
            "(within about 1–5 hours by road), here are some of the best options:"
        )
        out.append("")

        # 2. Hero image gallery (side-by-side cards) — only images that really exist on Wikipedia
        hero_places = (discover_result["popular"] + discover_result["medium"])[:6]
        gallery: list[tuple[str, str, str]] = []  # (name, img, link)
        for p in hero_places:
            img, link, _ = _place_media(p["name"], city)
            if img:
                gallery.append((p["name"], img, link))

        if gallery:
            # Marker the frontend renders as a horizontal card row
            out.append("<!-- gallery:start -->")
            for name, img, link in gallery:
                out.append(f"[![{name}]({img})]({link})")
            out.append("<!-- gallery:end -->")
            out.append("")

        risk_text = {
            "Low": "Generally safe for tourists.",
            "Medium": "Stay alert and follow local guidance.",
            "High": "Visit only with proper precautions.",
        }

        # 3. Numbered sections (Popular / Medium / Hidden combined & numbered like ChatGPT)
        all_places = (
            discover_result["popular"]
            + discover_result["medium"]
            + discover_result["hidden"]
        )

        for idx, place in enumerate(all_places, start=1):
            crowd = predict_crowd(city, place["popularity"], place["best_time"])
            img, wiki_or_maps, latlon = _place_media(place["name"], city)
            #adding new chnage sfrom codex 
            # Persist the exact media resolved for the AI Chat response.
            # AttractionBuilder runs immediately after ResponseBuilder.build(), so it
            # can return these same values to the planner cards.
            place["image"] = img or ""
            place["wiki_url"] = wiki_or_maps or ""

            if latlon:
                place["lat"], place["lon"] = latlon
                #until this codex changes 
            place_link = _place_link(place["name"], city, latlon)

            # Numbered heading like "1. Amboli (85 km, ~2 hours)" — clickable → Leaflet
            distance = place.get("distance")
            duration = place.get("travel_time") or place.get("duration") or ""
            suffix_bits = []
            if distance:
                suffix_bits.append(f"{distance} km")
            if duration and "hour" in str(duration).lower():
                suffix_bits.append(f"~{duration}")
            suffix = f" ({', '.join(suffix_bits)})" if suffix_bits else ""

            out.append(f"### [{idx}. {place['name']}{suffix}]({place_link})")
            out.append("")

            # Only render image if Wikipedia gave us a real one
            if img:
                out.append(f"[![{place['name']}]({img})]({wiki_or_maps})")
                out.append("")

            if place.get("description"):
                out.append(place["description"])
                out.append("")

            out.append(f"- 📂 **Category:** {place['category']}")
            out.append(f"- 🛡 **Risk:** {risk_text.get(place['risk'], place['risk'])}")
            out.append(f"- 👨‍👩‍👧 **Family Friendly:** {'Yes' if place['family'] else 'No'}")
            out.append(f"- 🕒 **Best Time:** {place['best_time']}")
            out.append(f"- ⏳ **Recommended Duration:** {place['duration']}")
            out.append(
                f"- 👥 **Expected Crowd:** {crowd['emoji']} {crowd['crowd']} "
                f"(score {crowd['score']})"
            )
            if crowd["reasons"]:
                out.append(f"- 📌 **Reason:** {', '.join(crowd['reasons'])}")
            out.append(f"- 💡 **Advice:** {crowd['advice']}")
            out.append("")

        # 4. Nearby destinations (also numbered continuing style)
        nearby = NearbyService.get_nearby_places(city)
        if nearby:
            out.append("---")
            out.append("")
            out.append("### If you have more time (4–6 hours)")
            out.append("")
            for place in nearby:
                trip_types = ", ".join(place["trip_types"]) if place["trip_types"] else "General Tourism"
                activities = ", ".join(place["activities"][:3]) if place["activities"] else "Sightseeing"

                img, wiki_or_maps, latlon = _place_media(place["name"], place.get("region", ""))
                place_link = _place_link(place["name"], place.get("region", city), latlon)

                out.append(
                    f"- [**{place['name']}**]({place_link}) "
                    f"({place['distance']} km) — {trip_types}. "
                    f"Popular activities: {activities}. "
                    f"Recommended stay: {place['ideal_days']} day(s)."
                )
            out.append("")

        # 5. AI Recommendation
        out.append("---")
        out.append("")
        out.append("### Recommended trips based on duration")
        out.append("")
        if discover_result["hidden"]:
            out.append(
                f"- **1 day:** popular attractions in {city}"
            )
            out.append(
                "- **2 days:** mix of popular + less crowded spots"
            )
            out.append(
                "- **3–4 days:** add hidden gems and nearby destinations for a full experience"
            )
        else:
            out.append(
                "Start early to avoid crowds at major attractions and keep sufficient time "
                "at each location instead of rushing your itinerary."
            )
        out.append("")

        # 6. Travel tips
        out.append("---")
        out.append("")
        out.append("### Travel tips")
        out.append("")
        out.append("- Carry drinking water.")
        out.append("- Wear comfortable walking shoes.")
        out.append("- Keep digital payment options ready.")
        out.append("- Follow local safety instructions.")
        out.append("")

        return "\n".join(out)
