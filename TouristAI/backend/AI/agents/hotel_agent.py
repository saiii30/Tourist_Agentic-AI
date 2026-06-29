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

        for place in data["places"][:5]:
            name = place.get("displayName", {}).get("text", "N/A")
            rating = place.get("rating", "N/A")
            reviews = place.get("userRatingCount", 0)
            address = place.get(
                "formattedAddress",
                "Address not available"
            )
            website = place.get("websiteUri", "Not available")
            photo_url = None
            photos = place.get("photos")
            if photos:
                photo_name = photos[0].get("name")
                photo_url = get_place_photo(photo_name, api_key)

            lines.append(f"🏨 {name}")
            lines.append(f"⭐ Rating: {rating} ({reviews} reviews)")
            lines.append(f"📍 Address: {address}")

            if website != "Not available":
                lines.append(f"🌐 Website: {website}")
            if photo_url:
                lines.append(f"![{name}]({photo_url})")

            lines.append("")

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
        return {
            "message": "I need to know which city you are visiting."
        }

    # Google Places
    google_results = get_hotels_from_google(
        city,
        budget,
        travelers
    )

    if google_results:
        # Save the successful Google response to RAG for future queries
        try:
            from rag_service import save_to_rag
            save_to_rag(question, google_results)
            print("✅ Saved Google Places response to RAG.")
        except Exception as e:
            print(f"⚠️ Could not save Google response to RAG: {e}")

        return {
            "source": "google_places",
            "city": city,
            "travelers": travelers,
            "hotels": google_results
        }

    # RAG Fallback
    print("⚠️ Google failed. Using RAG.")

    try:
        from rag_service import get_answer

        ans = get_answer(question)

        if isinstance(ans, dict):
            answer = ans.get("answer")
        else:
            answer = str(ans)

        return {
            "source": "rag",
            "answer": answer
        }

    except Exception as e:
        print("RAG Error:", str(e))

        return {
            "source": "fallback",
            "answer": f"Currently, I cannot fetch hotel recommendations for {city}."
        }


# Example
if __name__ == "__main__":
    result = hotel_agent(
        question="Suggest hotels in Madurai",
        city="Madurai",
        budget="medium",
        travelers=2
    )

    print(json.dumps(result, indent=4))