import os
import json
import urllib.request
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

            lines.append(f"🍽️ {name}")
            lines.append(f"⭐ Rating: {rating} ({reviews} reviews)")
            lines.append(f"💰 Price Level: {price}")
            lines.append(f"📍 Address: {address}")
            if photo_url:
                lines.append(f"![{name}]({photo_url})")
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
        return (
            "I need to know which city you are visiting "
            "to suggest restaurants."
        )

    # Try Google Places first
    google_results = get_restaurants_from_google(
        city,
        budget,
        interests
    )

    if google_results:
        print("✅ Found restaurant recommendations from Google Places API.")
        return google_results

    # Fallback to RAG
    print("⚠️ Google Places API failed or returned no results.")
    print("⚠️ Falling back to RAG service.")

    try:
        from rag_service import get_answer

        ans = get_answer(question)

        if isinstance(ans, dict):
            return ans.get("answer")

        return ans

    except Exception as e:
        print(f"❌ Error in restaurant_agent fallback: {e}")
        return (
            f"Currently, I cannot fetch restaurant "
            f"recommendations for {city}."
        )


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