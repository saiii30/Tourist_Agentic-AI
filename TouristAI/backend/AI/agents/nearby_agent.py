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

import base64
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote



def get_image_from_website(url, max_images=20):
    """
    Returns up to max_images image URLs from a website.
    """

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0 Safari/537.36"
            )
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=20,
            allow_redirects=True,
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        images = []
        seen = set()

        def add_image(src):
            if not src:
                return

            src = src.strip()

            if src.startswith("data:"):
                return

            full = urljoin(url, src)

            # Ignore icons/logos/svg
            if any(
                x in full.lower()
                for x in [
                    ".svg",
                    "logo",
                    "icon",
                    "favicon",
                    "sprite",
                ]
            ):
                return

            if full not in seen:
                seen.add(full)
                images.append(full)

        # -----------------------
        # OpenGraph
        # -----------------------
        og = soup.find("meta", property="og:image")
        if og:
            add_image(og.get("content"))

        # -----------------------
        # Twitter
        # -----------------------
        twitter = soup.find("meta", attrs={"name": "twitter:image"})
        if twitter:
            add_image(twitter.get("content"))

        # -----------------------
        # Picture source tags
        # -----------------------
        for source in soup.find_all("source"):
            add_image(source.get("srcset"))

        # -----------------------
        # IMG tags
        # -----------------------
        for img in soup.find_all("img"):

            attrs = [
                "src",
                "data-src",
                "data-lazy-src",
                "data-original",
                "data-image",
                "data-large-image",
                "data-srcset",
                "srcset",
            ]

            for attr in attrs:

                value = img.get(attr)

                if not value:
                    continue

                # srcset contains multiple URLs
                if attr in ["srcset", "data-srcset"]:
                    for item in value.split(","):
                        add_image(item.strip().split(" ")[0])
                else:
                    add_image(value)

        return images[:max_images]

    except Exception as e:
        print("Website image error:", e)
        return []

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
        "limit": 10,
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
                photo_urls = []

            if website:
                print(f"Getting images from: {website}")
                photo_urls = get_image_from_website(website, max_images=20)
                print("Images:", photo_urls)

                item_lines = [f"**{name}**"]
                item_lines.append(f"⭐ Rating: {rating}") # Foursquare doesn't provide review counts in basic search
                item_lines.append(f"📍 Address: {address}")

                if address != "Address not available":
                    map_query = urllib.parse.quote_plus(f"{name}, {address}")
                    map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
                    item_lines.append(f"[View Map]({map_url})") # No emoji

                if website != "Not available":
                    item_lines.append(f"[Visit Website]({website})") # No emoji
                if photo_urls:
                    for photo in photo_urls:
                        item_lines.append(f"![{name}]({photo})")

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
    field_mask = (
    "places.id,"
    "places.displayName,"
    "places.formattedAddress,"
    "places.location,"
    "places.types,"
    "places.primaryType,"
    "places.rating,"
    "places.userRatingCount,"
    "places.priceLevel,"
    "places.websiteUri,"
    "places.googleMapsUri,"
    "places.nationalPhoneNumber,"
    "places.internationalPhoneNumber,"
    "places.businessStatus,"
    "places.regularOpeningHours,"
    "places.currentOpeningHours,"
    "places.photos,"
    "places.parkingOptions,"
    "places.paymentOptions,"
    "places.accessibilityOptions,"
    "places.takeout,"
    "places.delivery,"
    "places.dineIn,"
    "places.servesBreakfast,"
    "places.servesLunch,"
    "places.servesDinner,"
    "places.servesBeer,"
    "places.servesWine,"
    "places.servesVegetarianFood,"
    "places.allowsDogs,"
    "places.goodForChildren,"
    "places.goodForGroups,"
    "places.editorialSummary"
    )
    
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
            for i, place in enumerate(data["places"][:10], 1):
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

                # Phone numbers
                phone = place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber")
                if phone:
                    item_lines.append(f"📞 Phone: {phone}")

                hours = (
                place.get("currentOpeningHours", {}).get("weekdayDescriptions")
                or place.get("regularOpeningHours", {}).get("weekdayDescriptions")
                or []
                )

                if hours:
                    item_lines.append("🕒 Hours:")
                    for h in hours:
                        item_lines.append(f"🕒 {h}")

                # Editorial summary
                editorial = place.get("editorialSummary", {}).get("text")
                if editorial:
                    item_lines.append(f"📝 {editorial}")

                # Business status
                business_status = place.get("businessStatus")
                if business_status:
                    status_text = "✅ Open" if business_status == "OPERATIONAL" else f"⚠️ {business_status}"
                    item_lines.append(status_text)

                # Good for children
                if place.get("goodForChildren"):
                    item_lines.append("👶 Good for children")

                # Good for groups
                if place.get("goodForGroups"):
                    item_lines.append("👥 Good for groups")

                # Accessibility options
                accessibility = place.get("accessibilityOptions", {})
            access_info = [
                "wheelchair accessible parking" for k, v in accessibility.items() if k == "wheelchairAccessibleParking" and v
            ] + [
                "wheelchair accessible entrance" for k, v in accessibility.items() if k == "wheelchairAccessibleEntrance" and v
            ]
            if access_info:
                item_lines.append(f"♿ {', '.join(access_info).capitalize()}")

                # Payment options
                payment = place.get("paymentOptions", {})
            payment_methods = [
                "credit cards" for k, v in payment.items() if k == "acceptsCreditCards" and v
            ] + [
                "debit cards" for k, v in payment.items() if k == "acceptsDebitCards" and v
            ] + [
                "cash only" for k, v in payment.items() if k == "acceptsCashOnly" and v
            ]

            if payment_methods:
                item_lines.append(f"💳 Accepts {', '.join(payment_methods)}")


                

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