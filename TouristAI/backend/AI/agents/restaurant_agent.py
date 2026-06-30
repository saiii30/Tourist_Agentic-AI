import os
import json
import urllib.request
import urllib.error
import urllib.parse
import base64

def get_unsplash_photo(query: str) -> str | None:
    """
    Fetches a generic photo from Unsplash based on a query.
    Returns a direct URL to the image.
    """
    unsplash_api_key = os.getenv("UNSPLASH_API_KEY")
    if not unsplash_api_key:
        print("⚠️ UNSPLASH_API_KEY not found. Skipping Unsplash fallback.")
        return None

    search_url = "https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "per_page": 1,
        "orientation": "landscape",
        "client_id": unsplash_api_key
    }
    encoded_params = urllib.parse.urlencode(params)
    full_url = f"{search_url}?{encoded_params}"

    try:
        req = urllib.request.Request(full_url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data and data.get("results"):
                print(f"✅ Found Unsplash fallback image for '{query}'")
                return data["results"][0]["urls"]["regular"]
            return None
    except Exception as e:
        print(f"❌ Unsplash API Error for query '{query}': {e}")
        return None

def get_place_photo(photo_name: str, api_key: str):
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

        with urllib.request.urlopen(photo_uri) as response:
            image_data = response.read()
            return f"data:image/jpeg;base64,{base64.b64encode(image_data).decode('utf-8')}"

    except Exception as e:
        print("Photo Error:", e)
        return None
        
def get_restaurants_from_google(city: str, budget: str, interests: str) -> str | None:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")

    if not api_key:
        print("❌ GOOGLE_PLACES_API_KEY not found.")
        return None

    # Build search query
    query_parts = [f"best restaurants in {city}"]

    if interests and interests.lower() != "none":
        query_parts.append(interests)

    if budget and budget.lower() != "none":
        query_parts.append(f"{budget} budget")

    query = " ".join(query_parts)

    url = "https://places.googleapis.com/v1/places:searchText"

    field_mask = (
        "places.displayName,"
        "places.rating,"
        "places.userRatingCount,"
        "places.formattedAddress,"
        "places.priceLevel,"
        "places.photos,"
        "places.websiteUri"
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

    print("\n========== GOOGLE RESTAURANT REQUEST ==========")
    print("Query:", query)
    print("Payload:", payload)
    print("===============================================\n")

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        print("\n========== GOOGLE RESPONSE ==========")
        print(json.dumps(data, indent=2))
        print("=====================================\n")

        if not data.get("places"):
            print("⚠️ No restaurants found.")
            return None

        lines = []

        for place in data["places"][:5]:
            name = place.get("displayName", {}).get("text", "N/A")
            rating = place.get("rating", "N/A")
            reviews = place.get("userRatingCount", 0)
            address = place.get(
                "formattedAddress",
                "Address not available"
            )
            price = place.get("priceLevel", "N/A")
            photo_url = None
            photos = place.get("photos")
            if photos:
                photo_name = photos[0].get("name")
                photo_url = get_place_photo(photo_name, api_key)
            
            # Fallback to Unsplash if Google Places photo is not available
            if not photo_url:
                photo_url = get_unsplash_photo(f"{name} {city} restaurant food")

            lines.append(f"🍽️ {name}")
            lines.append(f"⭐ Rating: {rating} ({reviews} reviews)")
            lines.append(f"💰 Price Level: {price}")
            lines.append(f"📍 Address: {address}")

            if address != "Address not available":
                map_query = urllib.parse.quote_plus(address)
                map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
                lines.append(f"🗺️ [View Map]({map_url})")

            website = place.get("websiteUri", "Not available")
            if website != "Not available":
                lines.append(f"🌐 [Visit Website]({website})")

            # Ensure photo_url is not None for markdown, or it will render an empty image tag
            lines.append(f"![{name}]({photo_url or ''})")
                
            lines.append("")

        print("✅ Google Places API call successful.")

        return "\n".join(lines)

    except urllib.error.HTTPError as e:
        print("\n========== GOOGLE HTTP ERROR ==========")
        print("Status Code:", e.code)

        try:
            error_body = e.read().decode("utf-8")
            print("Google Error Response:")
            print(error_body)
        except Exception:
            pass

        print("=======================================\n")
        return None

    except urllib.error.URLError as e:
        print("\n========== GOOGLE URL ERROR ==========")
        print("Reason:", e.reason)
        print("======================================\n")
        return None

    except Exception as e:
        print("\n========== UNEXPECTED ERROR ==========")
        print(str(e))
        print("======================================\n")
        return None


def restaurant_agent(
    question,
    city="None",
    interests="None",
    budget="None"
):
    if city == "None":
        return {"message": "I need to know which city you are visiting to suggest restaurants."}

    # 1. First, try to get a cached answer from the RAG service (FAISS DB only)
    try:
        from rag_service import get_answer
        rag_result = get_answer(question, check_rag_only=True)
        if rag_result:
            print("✅ Found restaurant recommendations from RAG (FAISS DB).")
            return rag_result
    except Exception as e:
        print(f"⚠️ Error checking RAG for restaurants: {e}")

    # 2. If RAG is empty, try the Google Places API
    print("ℹ️ No results in RAG. Checking Google Places API for restaurants.")
    google_results = get_restaurants_from_google(
        city, budget, interests
    )
    if google_results:
        # Save the successful Google response to RAG for future queries
        try:
            from rag_service import save_to_rag
            save_to_rag(question, google_results)
            print("✅ Saved Google Places response to RAG.")
        except Exception as e:
            print(f"⚠️ Could not save Google response to RAG: {e}")
        return {"source": "google_places", "answer": google_results}

    # 3. As a final fallback, call the RAG service again, which will now use the Groq LLM
    print("⚠️ Google Places API also failed. Falling back to Groq LLM.")
    try:
        from rag_service import get_answer
        return get_answer(question)
    except Exception as e:
        print(f"❌ Final fallback to Groq failed: {e}")
        return {"message": f"Sorry, I'm having trouble finding restaurant recommendations for {city} right now."}


# Test directly
if __name__ == "__main__":
    result = restaurant_agent(
        question="Best restaurants in Chennai",
        city="Chennai",
        interests="South Indian Food",
        budget="Budget"
    )

    print("\n========== FINAL RESULT ==========")
    print(result)
    print("==================================")