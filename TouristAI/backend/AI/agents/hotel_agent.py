import os
import json
import urllib.request
import urllib.error
import urllib.parse
import base64
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

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

    return None


def get_hotels_from_google(city: str, budget: str, travelers: int) -> str | None:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")

    if not api_key:
        print("❌ GOOGLE_PLACES_API_KEY not found.")
        return None

    query = f"best hotels in {city}"

    if budget and budget.lower() != "none":
        query = f"{budget} budget hotels in {city}"

    url = "https://places.googleapis.com/v1/places:searchText"

    field_mask = (
        "places.displayName,"
        "places.rating,"
        "places.userRatingCount,"
        "places.formattedAddress,"
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

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        print(json.dumps(data, indent=2))

        if not data.get("places"):
            print("⚠️ No hotels found.")
            return None

        lines = []

        for i, place in enumerate(data["places"][:5], 1):
            print(place)
            name = place.get("displayName", {}).get("text", "N/A")
            rating = place.get("rating", "N/A")
            reviews = place.get("userRatingCount", 0)
            address = place.get("formattedAddress", "Address not available")
            website = place.get("websiteUri", "Not available")
            
            photo_url = None

            website = place.get("websiteUri")
            photos = place.get("photos")

            # 1. TRY WEBSITE IMAGE FIRST
            # if website:
            #     photo_url = get_image_from_website(website)
            


            item_lines = [f"**{name}**"]
            item_lines.append(f"⭐ Rating: {rating} ({reviews} reviews)")
            item_lines.append(f"📍 Address: {address}")
            
            if address != "Address not available":
                map_query = urllib.parse.quote_plus(address)
                map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
                item_lines.append(f"[View Map]({map_url})")
                
            if website != "Not available":
                item_lines.append(f"[Visit Website]({website})")

            if photo_url:
                item_lines.append(f"![{name}]({photo_url})")

            lines.append(f"{i}. {chr(10).join(item_lines)}")

        print("✅ Hotels fetched successfully.")
       

        return "\n".join(lines)

    except urllib.error.HTTPError as e:
        print("Status:", e.code)
        print(e.read().decode("utf-8"))
        return None

    except Exception as e:
        print("Error:", str(e))
        return None


def hotel_agent(question, city="None", budget="None", travelers=1):
    if city == "None":
        return {"message": "I need to know which city you are visiting."}

    # 1. First, try to get a cached answer from the RAG service (FAISS DB only)
    try:
        from rag_service import get_answer
        rag_result = get_answer(question, check_rag_only=True)
        if rag_result:
            print("✅ Found hotel recommendations from RAG (FAISS DB).")
            return rag_result
    except Exception as e:
        print(f"⚠️ Error checking RAG for hotels: {e}")

    # 2. If RAG is empty, try the Google Places API
    print("ℹ️ No results in RAG. Checking Google Places API for hotels.")
    google_results = get_hotels_from_google(
        city, budget, travelers
    )
    if google_results:
        # Save the successful Google response to RAG for future queries
        try:
            from rag_service import save_to_rag
            save_to_rag(question, google_results)
            print("✅ Saved Google Places response to RAG.")
        except Exception as e:
            print(f"⚠️ Could not save Google response to RAG: {e}")
        return {"source": "google_places", "hotels": google_results}

    # 3. As a final fallback, call the RAG service again, which will now use the Groq LLM
    print("⚠️ Google Places API also failed. Falling back to Groq LLM.")
    try:
        from rag_service import get_answer
        return get_answer(question)
    except Exception as e:
        print(f"❌ Final fallback to Groq failed: {e}")
        return {"message": f"Sorry, I'm having trouble finding hotel recommendations for {city} right now."}


# Example
if __name__ == "__main__":
    result = hotel_agent(
        question="Suggest hotels in Madurai",
        city="Madurai",
        budget="medium",
        travelers=2
    )

    print(json.dumps(result, indent=4))