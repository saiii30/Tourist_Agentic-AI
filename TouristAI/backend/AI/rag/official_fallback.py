# backend/AI/rag/official_fallback.py
import re
from urllib.parse import quote_plus


DESTINATION_ALIASES = {
    "andhra pradesh": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jammu": "Jammu and Kashmir",
    "kashmir": "Jammu and Kashmir",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "ladakh": "Ladakh",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "orissa": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal",
    "madurai": "Madurai",
    "kanyakumari": "Kanniyakumari",
    "kanniyakumari": "Kanniyakumari",
    "ooty": "Ooty",
    "kodaikanal": "Kodaikanal",
}

STATE_TOURISM_URLS = {
    "Goa": "https://goa-tourism.com",
    "Kerala": "https://www.keralatourism.org",
    "Karnataka": "https://www.karnatakatourism.org",
    "Rajasthan": "https://www.tourism.rajasthan.gov.in",
    "Tamil Nadu": "https://tamilnadutourism.tn.gov.in",
    "Uttar Pradesh": "https://uptourism.gov.in",
    "Delhi": "https://delhitourism.gov.in",
}


def slugify_destination(destination: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", destination.lower()).strip("-")


def infer_requested_destination(query: str) -> str | None:
    lower = (query or "").lower()
    for alias, destination in sorted(DESTINATION_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", lower):
            return destination
    return None


def build_official_fallback(query: str, destination: str | None = None) -> dict:
    destination = destination or infer_requested_destination(query) or "this destination"
    encoded_query = quote_plus(f"{destination} tourism")
    incredible_slug = slugify_destination(destination)

    links = [
        {
            "name": f"Incredible India - {destination}",
            "url": f"https://www.incredibleindia.gov.in/en/{incredible_slug}",
        },
        {
            "name": "Incredible India search",
            "url": f"https://www.incredibleindia.gov.in/en/search?keyword={quote_plus(destination)}",
        },
        {
            "name": "Government tourism web search",
            "url": f"https://www.google.com/search?q={quote_plus(destination + ' official tourism government')}",
        },
    ]

    state_url = STATE_TOURISM_URLS.get(destination)
    if state_url:
        links.insert(1, {"name": f"{destination} official tourism", "url": state_url})

    answer_lines = [
        "**RAG Knowledge Check**",
        "",
        f"I do not have verified indexed RAG knowledge for **{destination}** yet.",
        "",
        "Use these official sources, then add the best page or PDF to the RAG source registry:",
        "",
    ]
    answer_lines.extend(f"- [{link['name']}]({link['url']})" for link in links)

    return {
        "destination": destination,
        "answer": "\n".join(answer_lines),
        "links": links,
    }
