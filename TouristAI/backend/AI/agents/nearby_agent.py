import os
import json
import urllib.request
import urllib.parse
from rag_service import client
import urllib.error
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
            return None
            
        # Then, download the image data from the URI and encode it as Base64
        with urllib.request.urlopen(photo_uri) as response:
            image_data = response.read()
            # Return a data URI that the browser can render directly
            return f"data:image/jpeg;base64,{base64.b64encode(image_data).decode('utf-8')}"
    except Exception as e:
        print("Photo Error:", e)
        return None

def get_places_from_foursquare(city: str, interests: str) -> str | None:
    """
    Fetches nearby places from the Foursquare API.
    """
    api_key = os.getenv("FOURSQUARE_API_KEY")
    if not api_key:
        print("⚠️ FOURSQUARE_API_KEY not found. Skipping Foursquare search.")
        return None

    query_parts = [interests] if interests and interests.lower() != "none" else ["tourist attractions"]
    query = " ".join(query_parts)

    url = "https://api.foursquare.com/v3/places/search"
    params = {
        "query": query,
        "near": city,
        "limit": 5,
        "fields": "fsq_id,name,location,rating,website,photos"
    }
    headers = {
        "Accept": "application/json",
        "Authorization": api_key
    }

    try:
        req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        if data and data.get("results"):
            print("✅ Foursquare API call successful, found nearby places.")
            lines = []
            for i, place in enumerate(data["results"][:5], 1): # Use enumerate
                name = place.get("name", "N/A")
                # Foursquare rating is out of 10, convert to 5-star scale
                rating = round(place.get("rating", 0) / 2, 1) if "rating" in place else "N/A"
                address = place.get("location", {}).get("formatted_address", "Address not available")
                website = place.get("website", "Not available")
                photo_url = None

                # if website != "Not available":
                #     photo_url = get_image_from_website(website)

                if place.get("photos"):
                    if not photo_url:
                        photo = place["photos"][0]
                        photo_url = f"{photo['prefix']}original{photo['suffix']}"

                item_lines = [f"**{name}**"]
                item_lines.append(f"⭐ Rating: {rating}") # Foursquare doesn't provide review counts in basic search
                item_lines.append(f"📍 Address: {address}")

                if address != "Address not available":
                    map_query = urllib.parse.quote_plus(f"{name}, {address}")
                    map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
                    item_lines.append(f"[View Map]({map_url})") # No emoji

                if website != "Not available":
                    item_lines.append(f"[Visit Website]({website})") # No emoji
                if photo_url:
                    item_lines.append(f"![{name}]({photo_url})")

                lines.append(f"{i}. {chr(10).join(item_lines)}") # Append as numbered item
            return "\n".join(lines)
        else:
            return None
    except Exception as e:
        print(f"❌ Foursquare API Error: {e}")
        return None
        
def get_places_from_google(city: str, interests: str) -> str | None:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print("GOOGLE_PLACES_API_KEY not found in environment. Skipping Google Places search.")
        return None

    # Construct the search query
    query_parts = [f"best tourist attractions in {city}"]
    if interests and interests.lower() != "none":
        query_parts.append(interests)
    
    query = " ".join(query_parts)
    
    # New Places API endpoint and parameters
    url = "https://places.googleapis.com/v1/places:searchText"
    field_mask = "places.displayName,places.rating,places.userRatingCount,places.formattedAddress,places.websiteUri,places.photos"
    
    post_data = json.dumps({"textQuery": query}).encode('utf-8')
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": field_mask,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        req = urllib.request.Request(url, data=post_data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        if data and data.get("places"):
            print("Google Places API call successful, found nearby places.")
            lines = []
            for i, place in enumerate(data["places"][:5], 1):
                name = place.get("displayName", {}).get("text", "N/A")
                rating = place.get("rating", "N/A")
                num_reviews = place.get("userRatingCount", 0)
                address = place.get("formattedAddress", "Address not available")
                website = place.get("websiteUri", "Not available")
                photo_url = None

                # if website != "Not available":
                #     photo_url = get_image_from_website(website)

                photos = place.get("photos")
                if not photo_url and photos:
                    photo_name = photos[0].get("name")
                    photo_url = get_place_photo(photo_name, api_key)

                item_lines = [f"**{name}**"]
                item_lines.append(f"⭐ Rating: {rating} ({num_reviews} reviews)")
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
            
            return "\n".join(lines)
        else:
            print(f"Google Places API returned no nearby places. Response: {data}")
            return None
    except urllib.error.HTTPError as e:
        print("Status Code:", e.code)
        print("Google Error Response:")
        print(e.read().decode("utf-8"))
        return None

    except Exception as e:
        print("Error:", str(e))
        return None

def nearby_agent(question, city="None", interests="None"):
    if city == "None":
        return {"message": "I need to know which city you are visiting to suggest nearby places."}

    # 1. Check RAG cache
    try:
        from rag_service import get_answer
        rag_result = get_answer(question, check_rag_only=True)
        if rag_result:
            print("✅ Found nearby place recommendations from RAG (FAISS DB).")
            return rag_result
    except Exception as e:
        print(f"⚠️ Error checking RAG for nearby places: {e}")

    # 2. Try Foursquare API
    print("ℹ️ Checking Foursquare API for nearby places.")
    foursquare_results = get_places_from_foursquare(city, interests)
    if foursquare_results:
        print("✅ Found results from Foursquare.")
        return {"source": "foursquare", "answer": foursquare_results}

    # 3. If Foursquare fails, try the Google Places API
    print("⚠️ Foursquare failed. Checking Google Places API for nearby places.")
    google_results = get_places_from_google(city, interests)
    if google_results:
        print("✅ Found results from Google Places.")
        # Save the successful Google response to RAG for future queries
        try:
            from rag_service import save_to_rag
            save_to_rag(question, google_results)
            print("✅ Saved Google Places response to RAG.")
        except Exception as e:
            print(f"⚠️ Could not save Google response to RAG: {e}")
        return {"source": "google_places", "answer": google_results}

    # 4. Final fallback to Groq LLM
    print("⚠️ All place APIs failed. Falling back to Groq LLM.")
    try:
        from rag_service import get_answer
        return get_answer(question)
    except Exception as e:
        print(f"❌ Final fallback to Groq failed: {e}")
        return {"message": f"Sorry, I'm having trouble finding sightseeing suggestions for {city} right now."}