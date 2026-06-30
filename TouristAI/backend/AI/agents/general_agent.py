from rag_service import get_answer, save_to_rag
import os
import urllib.request
import urllib.error
import urllib.parse
import json
import base64
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_image_from_website(url: str):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)

        soup = BeautifulSoup(res.text, "html.parser")

        # 1. OG IMAGE (BEST)
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]

        # 2. TWITTER IMAGE
        tw = soup.find("meta", property="twitter:image")
        if tw and tw.get("content"):
            return tw["content"]

        # 3. FIRST IMAGE TAG
        img = soup.find("img")
        if img and img.get("src"):
            img_url = img["src"]

            if img_url.startswith("/"):
                img_url = urljoin(url, img_url)

            return img_url

    except Exception as e:
        print("Website image error:", e)

def get_place_photo(photo_name: str, api_key: str):
    # First, get the photo URI from Google
    uri_url = (
        f"https://places.googleapis.com/v1/{photo_name}/media"
        f"?maxHeightPx=400"
        f"&skipHttpRedirect=true"
        f"&key={api_key}"
    )
    try:
        with urllib.request.urlopen(uri_url) as response:
            data = json.loads(response.read().decode("utf-8"))
            photo_uri = data.get("photoUri")
        
        if not photo_uri:
            print("⚠️ No photoUri in response")
            return None
            
        # Then, download the image data from the URI and encode it as Base64
        with urllib.request.urlopen(photo_uri) as response:
            image_data = response.read()
            # Return a data URI that the browser can render directly
            return f"data:image/jpeg;base64,{base64.b64encode(image_data).decode('utf-8')}"
    except Exception as e:
        print("Photo Error:", e)
        return None

def general_agent(question):
    """
    Flow:
    1. Check RAG
    2. Check Google Places
    3. Call Groq
    """

    # ------------------------------------
    # 1. Check RAG
    # ------------------------------------
    print("Checking RAG...")

    rag_result = get_answer(
        question,
        check_rag_only=True
    )

    if rag_result:
        print("Answer from RAG")
        return rag_result

    # ------------------------------------
    # 2. Check Google Places
    # ------------------------------------
    print("Checking Google Places...")

    google_result = search_google_places(question)

    if google_result:

        save_to_rag(
            question,
            google_result
        )

        return {
            "source": "Google Places",
            "answer": google_result
        }

    # ------------------------------------
    # 3. Call Groq
    # ------------------------------------
    print("Calling Groq...")

    groq_result = get_answer(
        question,
        check_rag_only=False
    )

    return groq_result

def search_google_places(query: str):
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")

    if not api_key:
        return None

    url = "https://places.googleapis.com/v1/places:searchText"

    field_mask = (
        "places.displayName,"
        "places.formattedAddress,"
        "places.rating,"
        "places.userRatingCount,"
        "places.websiteUri,"
        "places.photos"
    )

    payload = {
        "textQuery": query,
        "maxResultCount": 5
    }

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": field_mask
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))

        if not data.get("places"):
            return None

        lines = []

        for i, place in enumerate(data["places"][:5], 1): # Limit to top 5 and enumerate
            name = place.get("displayName", {}).get("text", "N/A")
            address = place.get("formattedAddress", "N/A")
            rating = place.get("rating", "N/A")
            reviews = place.get("userRatingCount", 0)
            website = place.get("websiteUri", "N/A")
            photo_url = None

            if website != "N/A":
                photo_url = get_image_from_website(website)

            item_lines = [f"**{name}**"]
            item_lines.append(f"⭐ Rating: {rating} ({reviews} reviews)")
            item_lines.append(f"📍 Address: {address}")

            if address != "N/A":
                map_query = urllib.parse.quote_plus(address)
                map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
                item_lines.append(f"[View Map]({map_url})")

            if website != "N/A":
                item_lines.append(f"[Visit Website]({website})")

            photos = place.get("photos")
            if not photo_url and photos:
                photo_name = photos[0]["name"]
                photo_url_google = get_place_photo(photo_name, api_key)
                if photo_url_google:
                    photo_url = photo_url_google
            
            if photo_url:
                item_lines.append(f"![{name}]({photo_url})")

            lines.append(f"{i}. {chr(10).join(item_lines)}")

        return "\n".join(lines)

    except Exception as e:
        print(e)
        return None