# backend/AI/services/live_web_search_service.py
import html
import os
import re
from typing import Any, Dict, List
from urllib.parse import quote_plus, unquote, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup


DUCKDUCKGO_SEARCH_URL = "https://duckduckgo.com/html/"
GOOGLE_SEARCH_URL = "https://www.google.com/search"
WIKIPEDIA_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
WIKIPEDIA_MEDIA_URL = "https://en.wikipedia.org/api/rest_v1/page/media-list/{title}"
WIKIMEDIA_COMMONS_API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0 Safari/537.36"
)

BEST_TIME_GUIDES = {
    "trichy": (
        "The best time to visit Trichy (Tiruchirappalli) is generally **November to February**, "
        "when temperatures are more comfortable for temples, Rockfort and outdoor sightseeing. "
        "**March to June** is usually very hot, so plan early-morning and evening visits if travelling then. "
        "**July to October** can bring monsoon rain and higher humidity; carry rain protection and allow extra travel time."
    ),
    "tiruchirappalli": (
        "The best time to visit Tiruchirappalli is generally **November to February**, when the weather is "
        "more comfortable for sightseeing. March to June is hot, while July to October can be humid with monsoon showers."
    ),
    "madurai": (
        "The most comfortable time to visit Madurai is generally **October to March**. Summers are very hot, "
        "so temple and heritage visits are easier in the early morning or evening from April to June."
    ),
    "salem": (
        "The most comfortable period for Salem is generally **November to February**. For nearby Yercaud, "
        "October to June is popular, while monsoon months offer greener scenery with intermittent rain."
    ),
    "kodaikanal": (
        "Kodaikanal is most popular from **March to June** for cool summer weather and from **September to October** "
        "for clearer post-monsoon scenery. Monsoon travel is quieter but comes with frequent rain and slippery roads."
    ),
    "udaipur": (
        "The best time to visit Udaipur is generally **October to March**, when temperatures are comfortable for "
        "palace visits, walking and lake activities. April to June is very hot; the monsoon brings greener scenery and fuller lakes."
    ),
}


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _unwrap_duckduckgo_url(url: str) -> str:
    parsed = urlparse(url or "")
    if "duckduckgo.com" not in parsed.netloc:
        return url

    uddg = parse_qs(parsed.query).get("uddg")
    if uddg:
        return unquote(uddg[0])
    return url


def _search_duckduckgo(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    response = requests.get(
        DUCKDUCKGO_SEARCH_URL,
        params={"q": query},
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results: List[Dict[str, str]] = []
    seen_urls = set()

    for result in soup.select(".result"):
        link = result.select_one(".result__a")
        snippet = result.select_one(".result__snippet")
        if not link:
            continue

        title = _clean_text(link.get_text(" "))
        href = _unwrap_duckduckgo_url(link.get("href", ""))
        body = _clean_text(snippet.get_text(" ") if snippet else "")

        if not title or not href or href in seen_urls:
            continue

        seen_urls.add(href)
        results.append({"title": title, "url": href, "snippet": body})
        if len(results) >= max_results:
            break

    return results


def _unwrap_google_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("/url?"):
        parsed = urlparse(url)
        q = parse_qs(parsed.query).get("q")
        if q:
            return q[0]
    return url


def _search_google(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    response = requests.get(
        GOOGLE_SEARCH_URL,
        params={"q": query, "hl": "en"},
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results: List[Dict[str, str]] = []
    seen_urls = set()

    for block in soup.select("div.g, div[data-sokoban-container]"):
        link = block.select_one("a[href]")
        heading = block.select_one("h3")
        if not link or not heading:
            continue

        href = _unwrap_google_url(link.get("href", ""))
        title = _clean_text(heading.get_text(" "))
        snippet_node = block.select_one(".VwiC3b, .IsZvec, span")
        snippet = _clean_text(snippet_node.get_text(" ") if snippet_node else "")

        if not title or not href or href.startswith("/") or href in seen_urls:
            continue

        seen_urls.add(href)
        results.append({"title": title, "url": href, "snippet": snippet})
        if len(results) >= max_results:
            break

    return results


def _search_wikipedia(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    response = requests.get(
        WIKIPEDIA_SEARCH_URL,
        params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": "1",
            "srlimit": max_results,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()

    search_items = response.json().get("query", {}).get("search", [])
    results: List[Dict[str, str]] = []

    for item in search_items[:max_results]:
        title = _clean_text(item.get("title", ""))
        if not title:
            continue

        page_url = f"https://en.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"
        snippet = _clean_text(html.unescape(re.sub(r"<[^>]+>", "", item.get("snippet", ""))))

        try:
            summary_res = requests.get(
                WIKIPEDIA_SUMMARY_URL.format(title=quote_plus(title.replace(" ", "_"))),
                headers={"User-Agent": USER_AGENT},
                timeout=8,
            )
            if summary_res.ok:
                summary_json = summary_res.json()
                snippet = _clean_text(summary_json.get("extract") or snippet)
                page_url = summary_json.get("content_urls", {}).get("desktop", {}).get("page") or page_url
                image_url = (
                    (summary_json.get("originalimage") or {}).get("source")
                    or (summary_json.get("thumbnail") or {}).get("source")
                )
            else:
                image_url = None
        except Exception as exc:
            print(f"[INFO] Wikipedia summary skipped for {title}: {exc}")
            image_url = None

        result = {"title": title, "url": page_url, "snippet": snippet}
        if image_url:
            result["image_url"] = image_url
        results.append(result)

    return results


def _wikipedia_summary_result(title: str) -> Dict[str, str] | None:
    try:
        response = requests.get(
            WIKIPEDIA_SUMMARY_URL.format(title=quote_plus(title.replace(" ", "_"))),
            headers={"User-Agent": USER_AGENT},
            timeout=8,
        )
        if not response.ok:
            return None

        data = response.json()
        extract = _clean_text(data.get("extract", ""))
        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
        page_title = _clean_text(data.get("title") or title)
        image_url = (
            (data.get("originalimage") or {}).get("source")
            or (data.get("thumbnail") or {}).get("source")
        )
        if not extract or not page_url:
            return None

        result = {"title": page_title, "url": page_url, "snippet": extract}
        if image_url:
            result["image_url"] = image_url
        page_images = _wikipedia_page_images(title)
        if len(page_images) < 3:
            page_images.extend(
                image for image in _commons_destination_images(title)
                if image not in page_images
            )
        if page_images:
            result["image_urls"] = page_images[:4]
        return result
    except Exception as exc:
        print(f"[INFO] Wikipedia exact summary skipped for {title}: {exc}")
        return None


def _wikipedia_page_images(title: str, limit: int = 4) -> List[str]:
    """Return photos belonging to the exact destination article."""
    try:
        response = requests.get(
            WIKIPEDIA_MEDIA_URL.format(title=quote_plus(title.replace(" ", "_"))),
            headers={"User-Agent": USER_AGENT},
            timeout=8,
        )
        if not response.ok:
            return []

        images: List[str] = []
        for item in response.json().get("items", []):
            if item.get("type") != "IMAGE":
                continue
            source = (item.get("original") or {}).get("source")
            if not source or source.lower().endswith((".svg", ".png")):
                continue
            if source not in images:
                images.append(source)
            if len(images) >= limit:
                break
        return images
    except Exception as exc:
        print(f"[INFO] Wikipedia media list skipped for {title}: {exc}")
        return []


def _commons_destination_images(title: str, limit: int = 4) -> List[str]:
    """Find additional photographs whose Commons file metadata matches the city."""
    destination = re.sub(r",.*$", "", title).strip()
    excluded = re.compile(r"\b(map|locator|logo|flag|seal|icon|symbol|diagram|district)\b", re.I)
    try:
        response = requests.get(
            WIKIMEDIA_COMMONS_API_URL,
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": f'"{destination}" filetype:bitmap',
                "gsrnamespace": 6,
                "gsrlimit": 20,
                "prop": "imageinfo",
                "iiprop": "url|mime",
                "iiurlwidth": 1200,
                "format": "json",
                "origin": "*",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        if not response.ok:
            return []

        images: List[str] = []
        pages = (response.json().get("query") or {}).get("pages", {})
        for page in pages.values():
            file_title = page.get("title", "")
            info = (page.get("imageinfo") or [{}])[0]
            mime = info.get("mime", "")
            if excluded.search(file_title) or mime not in {"image/jpeg", "image/webp"}:
                continue
            source = info.get("thumburl") or info.get("url")
            if source and source not in images:
                images.append(source)
            if len(images) >= limit:
                break
        return images
    except Exception as exc:
        print(f"[INFO] Commons destination images skipped for {title}: {exc}")
        return []


def _destination_overview_results(destination: str | None) -> List[Dict[str, str]]:
    if not destination:
        return []

    # Qualify ambiguous city names so results do not resolve to an unrelated
    # place with the same name (for example Salem, Oregon).
    destination_titles = {
        "salem": ["Salem, Tamil Nadu", "Salem district"],
    }
    candidates = destination_titles.get(destination.strip().lower(), [
        destination,
        f"Tourism in {destination}",
    ])
    results: List[Dict[str, str]] = []
    seen_urls = set()

    for title in candidates:
        result = _wikipedia_summary_result(title)
        if not result or result["url"] in seen_urls:
            continue
        seen_urls.add(result["url"])
        results.append(result)

    return results


def _destination_tokens(destination: str | None) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", (destination or "").lower())
        if len(token) > 2
    }


def _filter_destination_results(results: List[Dict[str, str]], destination: str | None) -> List[Dict[str, str]]:
    tokens = _destination_tokens(destination)
    if not tokens:
        return results

    filtered = []
    for item in results:
        haystack = f"{item.get('title', '')} {item.get('snippet', '')} {item.get('url', '')}".lower()
        if any(token in haystack for token in tokens):
            filtered.append(item)

    return filtered


def _search_live_web(
    query: str,
    destination: str | None = None,
    max_results: int = 5
) -> tuple[List[Dict[str, str]], List[str]]:
    errors: List[str] = []
    seeded_results = _destination_overview_results(destination)

    for provider_name, search_fn in (
        ("DuckDuckGo", _search_duckduckgo),
        ("Google", _search_google),
        ("Wikipedia", _search_wikipedia),
    ):
        try:
            results = search_fn(query, max_results=max_results)
            results = _filter_destination_results(results, destination)
            # A city overview is useful context, but it must not make an empty
            # provider search look successful. Continue to the next provider
            # until the user's actual question has matching results.
            if results and seeded_results:
                seen_urls = {item["url"] for item in seeded_results}
                results = seeded_results + [item for item in results if item.get("url") not in seen_urls]
            if results:
                return results, errors
            errors.append(f"{provider_name}: no parsed results")
        except Exception as exc:
            errors.append(f"{provider_name}: {exc}")

    if seeded_results:
        return seeded_results, errors

    return [], errors


def _summarize_with_groq(question: str, results: List[Dict[str, str]]) -> str | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        from groq import Groq

        source_text = "\n".join(
            f"{idx}. {item['title']}\nURL: {item['url']}\nSnippet: {item['snippet']}"
            for idx, item in enumerate(results, start=1)
        )
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You answer tourist questions using only the provided live web search snippets. "
                        "Be concise and practical. For broad destination questions, give a tourism overview: "
                        "what it is known for, key experiences, and travel context. Ignore snippets that are "
                        "not about the requested destination. Do not discuss current events unless the user asks."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nLive search results:\n{source_text}",
                },
            ],
            temperature=0.2,
        )
        return _clean_text(response.choices[0].message.content)
    except Exception as exc:
        print(f"[WARNING] Live web search summarization failed: {exc}")
        return None


def _fallback_answer(question: str, results: List[Dict[str, str]], destination: str | None = None) -> str:
    if re.search(r"\bbest\s+(?:time|season)|\bwhen\s+to\s+visit", question, re.I) and destination:
        guide = BEST_TIME_GUIDES.get(destination.strip().lower())
        if guide:
            return f"**Best time to visit {destination}**\n\n{guide}"

    usable_snippets = [
        item for item in results[:3]
        if item.get("snippet") and len(item["snippet"]) > 40
    ]

    if usable_snippets:
        lines = []
        if destination:
            lines.append(f"**About {destination}**")
        for item in usable_snippets:
            lines.append(f"- {item['snippet']}")
        return "\n".join(lines)

    lines = ["Here are the most relevant results:"]
    for item in results[:4]:
        snippet = f" - {item['snippet']}" if item.get("snippet") else ""
        lines.append(f"- [{item['title']}]({item['url']}){snippet}")
    return "\n".join(lines)


def answer_from_live_web(question: str, destination: str | None = None) -> Dict[str, Any]:
    search_query = question
    if destination and destination.lower() not in question.lower():
        search_query = f"{question} {destination}"
    if not re.search(r"\btourism|tourist|travel|official\b", search_query, re.I):
        search_query = f"{search_query} tourism travel"

    results, errors = _search_live_web(search_query, destination=destination)

    if not results:
        return {
            "has_answer": False,
            "answer": "",
            "sources": [],
            "error": "; ".join(errors) or "No live web results found.",
            "search_query": search_query,
        }

    summary = _summarize_with_groq(question, results)
    if summary and re.search(
        r"(?:don['’]t have|do not have|could not find|no relevant information|"
        r"search results provided|provided (?:snippet|snippets).*?(?:doesn['’]t|does not|do not) (?:include|contain)|"
        r"(?:snippet|snippets).*?(?:doesn['’]t|does not|do not) (?:include|contain))",
        summary,
        re.I,
    ):
        summary = None
    answer = summary or _fallback_answer(question, results, destination=destination)
    image_candidates: List[str] = []
    for item in results:
        image_candidates.extend(item.get("image_urls") or [])
        if item.get("image_url"):
            image_candidates.append(item["image_url"])
    image_urls = list(dict.fromkeys(image_candidates))[:4]

    return {
        "has_answer": True,
        "answer": answer,
        "sources": results,
        "image_url": image_urls[0] if image_urls else None,
        "image_urls": image_urls,
        "search_query": search_query,
        "errors": errors,
    }
