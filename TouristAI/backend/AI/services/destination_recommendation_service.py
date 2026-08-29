import json
import os
from typing import Any, Dict, List, Optional

from services.live_web_search_service import _search_live_web


def _build_search_query(origin: str, days: Optional[str], season: Optional[str], interests: Optional[str], target_region: Optional[str]) -> str:
    parts = ["best tourist destinations"]
    if target_region:
        parts.append(f"in {target_region}")
    parts.append(f"from {origin}")
    if days:
        parts.append(f"for a {days} day trip")
    if season:
        parts.append(f"during {season}")
    if interests:
        parts.append(f"for {interests}")
    parts.append("travel time itinerary")
    return " ".join(parts)


def _groq_recommendations(query: str, origin: str, days: Optional[str], season: Optional[str], interests: Optional[str], results: List[Dict[str, str]]) -> List[Dict[str, str]]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not results:
        return []
    try:
        from groq import Groq

        source_text = "\n".join(
            f"{index}. {item.get('title', '')}\nURL: {item.get('url', '')}\nSnippet: {item.get('snippet', '')}"
            for index, item in enumerate(results, start=1)
        )
        response = Groq(api_key=api_key).chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": (
                    "You are a travel recommendation engine. Use only the supplied live-search snippets. "
                    "Select up to four destinations that realistically fit the origin, duration and season. "
                    "Never select the origin itself. Return a JSON object with a recommendations array. "
                    "Each item must contain name, why, travel, and ideal strings. Return an empty array when evidence is insufficient."
                )},
                {"role": "user", "content": (
                    f"Search request: {query}\nOrigin: {origin}\nDays: {days or 'not specified'}\n"
                    f"Season: {season or 'not specified'}\nInterests: {interests or 'not specified'}\n\nLive results:\n{source_text}"
                )},
            ],
            temperature=0.15,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.choices[0].message.content or "{}")
        items = parsed.get("recommendations", []) if isinstance(parsed, dict) else []
        clean_items = []
        for item in items[:4]:
            if not isinstance(item, dict) or not item.get("name") or not item.get("why"):
                continue
            clean_items.append({
                "name": str(item["name"]).strip(),
                "why": str(item["why"]).strip(),
                "travel": str(item.get("travel") or "Check the route from your starting point").strip(),
                "ideal": str(item.get("ideal") or (f"{days} days" if days else "Flexible")).strip(),
            })
        return clean_items
    except Exception as exc:
        print(f"[WARNING] Dynamic destination recommendation failed: {exc}")
        return []


def _search_result_fallback(results: List[Dict[str, str]], origin: str) -> str:
    usable = [item for item in results if item.get("snippet") and len(item["snippet"]) > 50][:4]
    if not usable:
        return (
            "I couldn’t find enough current, source-backed destination options for those constraints. "
            "Try adding the number of days, travel month, or preferred travel distance."
        )
    lines = [f"**Current destination ideas from {origin}**", ""]
    for item in usable:
        lines.append(f"- **{item['title']}** — {item['snippet']}")
    lines.extend(["", "Tell me which option interests you and I’ll verify it and build the itinerary."])
    return "\n".join(lines)


def recommend_destinations(origin: Optional[str], days: Optional[str], season: Optional[str], interests: Optional[str] = None, target_region: Optional[str] = None) -> Dict[str, Any]:
    if not origin:
        return {
            "needs_clarification": True,
            "answer": "What city will you be travelling from? I’ll use it to suggest places that are realistic for your available time.",
            "options": [], "sources": [], "image_urls": [],
        }

    query = _build_search_query(origin, days, season, interests, target_region)
    results, errors = _search_live_web(query, destination=None, max_results=8)
    # Search engines can be poor at long constraint-heavy queries. Retry with
    # simpler region/season queries while preserving the user's actual scope.
    if not results and target_region:
        simpler_queries = [
            f"best places to visit in {target_region} {season or ''} tourism".strip(),
            f"{target_region} tourism destinations {season or ''}".strip(),
        ]
        for simpler_query in simpler_queries:
            retry_results, retry_errors = _search_live_web(simpler_query, destination=None, max_results=8)
            errors.extend(retry_errors)
            if retry_results:
                query = simpler_query
                results = retry_results
                break
    options = _groq_recommendations(query, origin, days, season, interests, results)

    if not options:
        answer = _search_result_fallback(results, origin)
    else:
        heading = f"Best trips from {origin}"
        if days:
            heading += f" for {days} days"
        if season:
            heading += f" in {season.lower()}"
        lines = [f"**{heading}**", ""]
        for option in options:
            lines.extend([
                f"### {option['name']}", f"- Why it fits: {option['why']}",
                f"- Travel: {option['travel']}", f"- Recommended stay: {option['ideal']}", "",
            ])
        lines.append("Choose one destination and I can verify the details and build a day-by-day itinerary.")
        answer = "\n".join(lines).strip()

    image_urls: List[str] = []
    for item in results:
        image_urls.extend(item.get("image_urls") or [])
        if item.get("image_url"):
            image_urls.append(item["image_url"])
    return {
        "needs_clarification": False, "answer": answer, "options": options,
        "sources": results[:4], "image_urls": list(dict.fromkeys(image_urls))[:4],
        "search_query": query, "errors": errors,
    }
