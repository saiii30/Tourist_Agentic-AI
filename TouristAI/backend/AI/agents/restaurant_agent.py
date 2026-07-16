import os
import json
import urllib.request
import urllib.error
import urllib.parse
import base64
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from dotenv import load_dotenv

# Load environment variables from possible locations to ensure API keys are populated
for env_path in [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
    os.path.abspath(os.path.join(os.getcwd(), ".env")),
    os.path.abspath(os.path.join(os.getcwd(), "backend", ".env")),
]:
    if os.path.exists(env_path):
        load_dotenv(env_path)


def get_image_from_website(url, max_images=1):
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

        
def get_restaurants_from_google(question: str, city: str, budget: str, interests: str) -> str | None:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")

    if not api_key:
        print("[ERROR] GOOGLE_PLACES_API_KEY not found.")
        return None

    # Build a more specific search query
    query_parts = [f"best restaurants in {city}"]

    # Add dietary preferences from the original question
    question_lower = question.lower()
    if "veg" in question_lower or "vegetarian" in question_lower:
        query_parts.append("vegetarian")
    elif "non-veg" in question_lower or "non vegetarian" in question_lower:
        query_parts.append("non-vegetarian")

    if interests and interests.lower() != "none":
        query_parts.append(interests)

    if budget and budget.lower() != "none":
        # Only append descriptive budget words, not raw numbers (which restrict Google Search results)
        if not any(char.isdigit() for char in budget):
            query_parts.append(f"{budget} budget")

    query = " ".join(query_parts)

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

        lines = []
        rests_data = []

        for i, place in enumerate(data["places"][:5], 1):
            rest_id = place.get("id", f"mock-rest-{i}")
            name = place.get("displayName", {}).get("text", "N/A")
            rating = place.get("rating", "N/A")
            reviews = place.get("userRatingCount", 0)
            address = place.get("formattedAddress", "Address not available")
            price = place.get("priceLevel", "N/A")
            website = place.get("websiteUri", "Not available")
            photo_urls = []

            # Get coordinates
            loc = place.get("location", {})
            lat = loc.get("latitude")
            lng = loc.get("longitude")

            if website:
                print(f"Getting images from: {website}")
                photo_urls = get_image_from_website(website, max_images=1)
                print("Images:", photo_urls)

            item_lines = [f"**{name}**"]
            item_lines.append(f"⭐ Rating: {rating} ({reviews} reviews)")
            item_lines.append(f"💰 Price Level: {price}")
            item_lines.append(f"📍 Address: {address}")

            # Phone numbers
            phone = place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber")
            if phone:
                item_lines.append(f"📞 Phone: {phone}")

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
            if accessibility:
                access_info = [
                    "wheelchair accessible parking" for k, v in accessibility.items() if k == "wheelchairAccessibleParking" and v
                ] + [
                    "wheelchair accessible entrance" for k, v in accessibility.items() if k == "wheelchairAccessibleEntrance" and v
                ]
                if access_info:
                    item_lines.append(f"♿ {', '.join(access_info).capitalize()}")

            # Payment options
            payment = place.get("paymentOptions", {})
            if payment:
                payment_methods = [
                    "credit cards" for k, v in payment.items() if k == "acceptsCreditCards" and v
                ] + [
                    "debit cards" for k, v in payment.items() if k == "acceptsDebitCards" and v
                ] + [
                    "cash only" for k, v in payment.items() if k == "acceptsCashOnly" and v
                ]
                if payment_methods:
                    item_lines.append(f"💳 Accepts {', '.join(payment_methods)}")

            # Dining options
            dining_options = []
            if place.get("servesBreakfast"):
                dining_options.append("Breakfast")
            if place.get("servesLunch"):
                dining_options.append("Lunch")
            if place.get("servesDinner"):
                dining_options.append("Dinner")
            if place.get("servesVegetarianFood"):
                dining_options.append("Vegetarian")
            if place.get("takeout"):
                dining_options.append("Takeout")
            if place.get("delivery"):
                dining_options.append("Delivery")
            if place.get("dineIn"):
                dining_options.append("Dine-in")
            if dining_options:
                item_lines.append(f"🍽️ {', '.join(dining_options)}")

            hours = (
                place.get("currentOpeningHours", {}).get("weekdayDescriptions")
                or place.get("regularOpeningHours", {}).get("weekdayDescriptions")
                or []
            )

            if hours:
                item_lines.append("🕒 Hours:")
                for h in hours:
                    item_lines.append(f"🕒 {h}")

            if address != "Address not available":
                map_query = urllib.parse.quote_plus(address)
                map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
                item_lines.append(f"[View Map]({map_url})")

            if website != "Not available":
                item_lines.append(f"[Visit Website]({website})")

            if photo_urls:
                for photo in photo_urls:
                    item_lines.append(f"![{name}]({photo})")

            lines.append(f"{i}. {chr(10).join(item_lines)}")

            rests_data.append({
                "restaurant_id": rest_id,
                "name": name,
                "rating": rating if isinstance(rating, (int, float)) else 4.2,
                "reviews": reviews,
                "address": address,
                "website": website,
                "latitude": lat,
                "longitude": lng,
                "price": price,
                "serves_breakfast": bool(place.get("servesBreakfast")),
                "serves_lunch": bool(place.get("servesLunch")),
                "serves_dinner": bool(place.get("servesDinner")),
                "serves_vegetarian": bool(place.get("servesVegetarianFood")),
                "hours": hours
            })

        print("[INFO] Google Places API call successful.")

        return {"text": "\n".join(lines), "data": rests_data}

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

    is_trip_plan = any(kw in question.lower() for kw in ["plan a", "trip", "itinerary", "vacation", "holiday"])

    # 1. First, try to get a cached answer from the RAG service (FAISS DB only)
    if not is_trip_plan:
        try:
            from rag_service import get_answer
            rag_result = get_answer(question, check_rag_only=True)
            if rag_result:
                print("[INFO] Found restaurant recommendations from RAG (FAISS DB).")
                return rag_result
        except Exception as e:
            print(f"[WARNING] Error checking RAG for restaurants: {e}")

    # 2. If RAG is empty, try the Google Places API
    print("[INFO] No results in RAG. Checking Google Places API for restaurants.")
    google_results = get_restaurants_from_google(
        question, city, budget, interests
    )
    if google_results:
        # Save the successful Google response to RAG for future queries
        try:
            from rag_service import save_to_rag
            save_to_rag(question, google_results["text"])
            print("[INFO] Saved Google Places response to RAG.")
        except Exception as e:
            print(f"[WARNING] Could not save Google response to RAG: {e}")
        return {"source": "google_places", "answer": google_results["text"], "data": google_results["data"]}

    # 3. As a final fallback, call the RAG service again, which will now use the Groq LLM
    print("[WARNING] Google Places API also failed. Falling back to Groq LLM.")
    try:
        from rag_service import get_answer
        return get_answer(question)
    except Exception as e:
        print(f"[ERROR] Final fallback to Groq failed: {e}")
        return {"message": f"Sorry, I'm having trouble finding restaurant recommendations for {city} right now."}