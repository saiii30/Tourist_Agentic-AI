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


def get_restaurants_from_google(
    question: str,
    city: str,
    budget: str,
    cuisine: str,
    diet: str,
    meal_time: str,
    family_friendly: str,
    outdoor_seating: str,
    allergies: str
) -> str | None:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")

    if not api_key:
        print("[ERROR] GOOGLE_PLACES_API_KEY not found.")
        return None

    # Build a highly specific search query from all the collected details
    query_parts = ["restaurants"]

    if cuisine and cuisine.lower() not in ["none", "any"]:
        query_parts.append(f"{cuisine} cuisine")

    query_parts.append(f"in {city}")

    if diet and diet.lower() not in ["none", "any"]:
        query_parts.append(diet)

    if meal_time and meal_time.lower() not in ["none", "any"]:
        query_parts.append(f"for {meal_time}")

    if family_friendly and family_friendly.lower() == "yes":
        query_parts.append("family-friendly")

    if budget and budget.lower() != "none":
        query_parts.append(f"{budget} budget")

    if outdoor_seating and outdoor_seating.lower() == "yes":
        query_parts.append("with outdoor seating")

    if allergies and allergies.lower() not in ["none", "any"]:
        query_parts.append(f"avoiding {allergies}")

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
        "maxResultCount": 10
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


        lines = []
        rests_data = []

        for i, place in enumerate(data["places"][:10], 1):
            rest_id = place.get("id", f"mock-rest-{i}")
            name = place.get("displayName", {}).get("text", "N/A")
            rating = place.get("rating", "N/A")
            reviews = place.get("userRatingCount", 0)
            address = place.get("formattedAddress", "Address not available")
            price = place.get("priceLevel", "N/A")
            website = place.get("websiteUri", "Not available")
            photos = place.get("photos", [])
            google_photo_name = photos[0].get("name") if photos else None
            photo_urls = []

            # Get coordinates
            loc = place.get("location", {})
            lat = loc.get("latitude")
            lng = loc.get("longitude")

            if website:
                photo_urls = get_image_from_website(website, max_images=1)
           

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
                "mapsUrl": place.get("googleMapsUri"),
                "phone": place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber"),
                "latitude": lat,
                "longitude": lng,
                "price": price,
                "googlePhotoName": google_photo_name,
                "photos": photo_urls,
                "serves_breakfast": bool(place.get("servesBreakfast")),
                "serves_lunch": bool(place.get("servesLunch")),
                "serves_dinner": bool(place.get("servesDinner")),
                "serves_vegetarian": bool(place.get("servesVegetarianFood")),
                "takeout": bool(place.get("takeout")),
                "delivery": bool(place.get("delivery")),
                "dineIn": bool(place.get("dineIn")),
                "goodForChildren": bool(place.get("goodForChildren")),
                "goodForGroups": bool(place.get("goodForGroups")),
                "allowsDogs": bool(place.get("allowsDogs")),
                "accessibility": place.get("accessibilityOptions", {}),
                "parking": place.get("parkingOptions", {}),
                "payment": place.get("paymentOptions", {}),
                "summary": editorial,
                "hours": hours
            })

        

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
    interests="None", # Retained for general keyword matching
    budget="None",
    cuisine="None",
    diet="None",
    meal_time="None",
    family_friendly="None",
    outdoor_seating="None",
    allergies="None"
):
    if city == "None":
        return {"message": "I need to know which city you are visiting to suggest restaurants."}

    is_trip_plan = any(kw in question.lower() for kw in ["plan a", "trip", "itinerary", "vacation", "holiday"])

    q_lower = (question or "").lower()
    d_lower = (diet or "").lower()
    is_non_veg = any(kw in q_lower or kw in d_lower for kw in ["non-veg", "non veg", "nonveg", "meat", "chicken", "mutton", "seafood", "fish"])
    is_pure_veg = not is_non_veg and any(kw in q_lower or kw in d_lower for kw in ["pure veg", "vegetarian", "veg", "swami"])

    # Use Google Places API as the primary restaurant source.
    print("[INFO] Checking Google Places API for restaurants.")
    google_results = get_restaurants_from_google(
        question=question,
        city=city,
        budget=budget,
        cuisine=cuisine or interests,
        diet=diet,
        meal_time=meal_time,
        family_friendly=family_friendly,
        outdoor_seating=outdoor_seating,
        allergies=allergies
    )
    if google_results:
        return {"source": "google_places", "answer": google_results["text"], "data": google_results["data"]}

    try:
        from services.trip_service import get_structured_restaurants
        llm_restaurants = get_structured_restaurants(city, budget or "Moderate")
        if llm_restaurants:
            return {
                "source": "llm_fallback",
                "answer": f"Recommended restaurants in {city} generated after Google Places was unavailable.",
                "data": llm_restaurants,
            }
    except Exception as e:
        print(f"[WARNING] LLM restaurant fallback failed: {e}")

    # Fallback default structured restaurants for city categorized by Veg / Non-Veg
    if is_pure_veg:
        fallback_rests = [
            {
                "id": f"fallback-veg-1-{city}",
                "name": f"Sree Sabarees Pure Veg {city}",
                "rating": 4.8,
                "reviews": 3200,
                "address": f"Town Hall Rd, {city}",
                "diet": "[Pure Veg]",
                "cuisine": "[Pure Veg] · South Indian Tiffin & Thali",
                "latitude": 9.9180,
                "longitude": 78.1170,
                "price_range": "₹150 - ₹400"
            },
            {
                "id": f"fallback-veg-2-{city}",
                "name": f"Murugan Idli Shop (100% Veg)",
                "rating": 4.7,
                "reviews": 4500,
                "address": f"West Masi Street, {city}",
                "diet": "[Pure Veg]",
                "cuisine": "[Pure Veg] · Soft Idlis & Dosa Delights",
                "latitude": 9.9175,
                "longitude": 78.1165,
                "price_range": "₹100 - ₹300"
            }
        ]
    elif is_non_veg:
        fallback_rests = [
            {
                "id": f"fallback-nonveg-1-{city}",
                "name": f"Amma Mess (Authentic Non-Veg)",
                "rating": 4.7,
                "reviews": 2800,
                "address": f"Alagar Kovil Main Rd, {city}",
                "diet": "[Non-Veg]",
                "cuisine": "[Non-Veg] · Chettinad Mutton & Fish Fry",
                "latitude": 9.9380,
                "longitude": 78.1350,
                "price_range": "₹300 - ₹800"
            },
            {
                "id": f"fallback-nonveg-2-{city}",
                "name": f"Simmakkal Konar Mess",
                "rating": 4.6,
                "reviews": 2100,
                "address": f"Simmakkal, {city}",
                "diet": "[Non-Veg]",
                "cuisine": "[Non-Veg] · Kari Dosa & Local Meat Dishes",
                "latitude": 9.9240,
                "longitude": 78.1210,
                "price_range": "₹250 - ₹700"
            }
        ]
    else:
        fallback_rests = [
            {
                "id": f"fallback-rest-1-{city}",
                "name": f"Sree Sabarees Pure Veg {city}",
                "rating": 4.8,
                "reviews": 3200,
                "address": f"Town Hall Rd, {city}",
                "diet": "[Pure Veg]",
                "cuisine": "[Pure Veg] · South Indian Tiffin",
                "latitude": 9.9180,
                "longitude": 78.1170,
                "price_range": "₹150 - ₹400"
            },
            {
                "id": f"fallback-rest-2-{city}",
                "name": f"Amma Mess (Famous Non-Veg)",
                "rating": 4.7,
                "reviews": 2800,
                "address": f"Alagar Kovil Main Rd, {city}",
                "diet": "[Non-Veg]",
                "cuisine": "[Non-Veg] · Chettinad Mutton & Fish Curry",
                "latitude": 9.9380,
                "longitude": 78.1350,
                "price_range": "₹300 - ₹800"
            }
        ]
    return {"source": "fallback", "answer": f"Recommended restaurants in {city}", "data": fallback_rests}
