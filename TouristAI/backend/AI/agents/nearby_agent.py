import os
import json
import urllib.request
import urllib.parse
from rag_service import client
import urllib.error

def get_place_photo(photo_name: str, api_key: str):
    url = (
        f"https://places.googleapis.com/v1/{photo_name}/media"
        f"?maxHeightPx=400"
        f"&skipHttpRedirect=true"
        f"&key={api_key}"
    )

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("photoUri")
    except Exception as e:
        print("Photo Error:", e)
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
            # Limit to top 3 results
            for place in data["places"][:5]:
                name = place.get("displayName", {}).get("text", "N/A")
                rating = place.get("rating", "N/A")
                num_reviews = place.get("userRatingCount", 0)
                address = place.get("formattedAddress", "Address not available")
                website = place.get("websiteUri", "Not available")
                photo_url = None
                photos = place.get("photos")
                if photos:
                    photo_name = photos[0].get("name")
                    photo_url = get_place_photo(photo_name, api_key)

                lines.append(f"🏛 {name}")
                lines.append(f"⭐ Rating: {rating} ({num_reviews} reviews)")
                lines.append(f"📍 Address: {address}")

                if website != "Not available":
                    lines.append(f"🌐 Website: {website}")
                if photo_url:
                    lines.append(f"![{name}]({photo_url})")

                lines.append("")
            
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
        print("Error:", str(neede))
        return None

def nearby_agent(question, city="None", interests="None"):
    if city == "None":
        return "I need to know which city you are visiting to suggest nearby places."
        
    # 1. Attempt to get data from Google Places API first
    google_results = get_places_from_google(city, interests)
    if google_results:
        print("Found nearby place recommendations from Google Places API.")
        # Save the successful Google response to RAG for future queries
        try:
            from rag_service import save_to_rag
            save_to_rag(question, google_results)
            print("✅ Saved Google Places response to RAG.")
        except Exception as e:
            print(f"⚠️ Could not save Google response to RAG: {e}")
        return google_results

    # 2. Fallback to RAG service (FAISS DB -> Groq LLM) if Google API fails
    print("Google Places API failed or returned no results. Falling back to RAG service.")
    try:
        from rag_service import get_answer
        ans = get_answer(question)
        return ans.get("answer") if isinstance(ans, dict) else ans
    except Exception as e:
        print(f"Error in nearby_agent fallback: {e}")
        return f"Currently, I cannot fetch sightseeing suggestions for {city}."