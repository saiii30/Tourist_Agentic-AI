import os
import json
import urllib.request
import urllib.parse

from rag_service import client
import urllib.error
import base64
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from dotenv import load_dotenv
from agents.discover_places_agent import discover_places, is_discover_query


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
            places_data = []

            for i, place in enumerate(data["places"][:5], 1):
                attraction_id = place.get("id", f"mock-attraction-{i}")
                name = place.get("displayName", {}).get("text", "N/A")
                rating = place.get("rating", "N/A")
                num_reviews = place.get("userRatingCount", 0)
                address = place.get("formattedAddress", "Address not available")
                website = place.get("websiteUri", "Not available")
                photo_url = None

                # Get coordinates
                loc = place.get("location", {})
                lat = loc.get("latitude")
                lng = loc.get("longitude")

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

                # Get photo name
                photos = place.get("photos", [])
                photo_name = photos[0].get("name") if photos else None

                if address != "Address not available":
                    map_query = urllib.parse.quote_plus(address)
                    map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
                    item_lines.append(f"[View Map]({map_url})")

                if website != "Not available":
                    item_lines.append(f"[Visit Website]({website})")

                if photo_url:
                    item_lines.append(f"![{name}]({photo_url})")

                lines.append(f"{i}. {chr(10).join(item_lines)}")

                places_data.append({
                    "attraction_id": attraction_id,
                    "name": name,
                    "rating": rating if isinstance(rating, (int, float)) else 4.2,
                    "reviews": num_reviews,
                    "address": address,
                    "website": website,
                    "mapsUrl": place.get("googleMapsUri"),
                    "phone": place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber"),
                    "latitude": lat,
                    "longitude": lng,
                    "types": place.get("types", []),
                    "primaryType": place.get("primaryType"),
                    "businessStatus": place.get("businessStatus"),
                    "accessibility": place.get("accessibilityOptions", {}),
                    "parking": place.get("parkingOptions", {}),
                    "hours": hours,
                    "editorial": editorial or "",
                    "googlePhotoName": photo_name
                })
            
            return {"text": "\n".join(lines), "data": places_data}
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

# def nearby_agent(question, city="None", interests="None"):
    
#     if city == "None":
#         return {"message": "I need to know which city you are visiting to suggest nearby places."}

#     is_trip_plan = any(kw in question.lower() for kw in ["plan a", "trip", "itinerary", "vacation", "holiday"])

#     # 1. Check RAG cache
#     if not is_trip_plan:
#         try:
#             from rag_service import get_answer
#             rag_result = get_answer(question, check_rag_only=True)
#             if rag_result:
#                 print("[INFO] Found nearby place recommendations from RAG (FAISS DB).")
#                 return rag_result
#         except Exception as e:
#             print(f"[WARNING] Error checking RAG for nearby places: {e}")


#     # 2. If  fails, try the Google Places API
#     print("[WARNING] Foursquare failed. Checking Google Places API for nearby places.")
#     google_results = get_places_from_google(city, interests)
#     if google_results:
#         print("[INFO] Found results from Google Places.")
#         # Save the successful Google response to RAG for future queries
#         try:
#             from rag_service import save_to_rag
#             save_to_rag(question, google_results["text"])
#             print("[INFO] Saved Google Places response to RAG.")
#         except Exception as e:
#             print(f"[WARNING] Could not save Google response to RAG: {e}")
#         return {"source": "google_places", "answer": google_results["text"], "data": google_results["data"]}

#     # 4. Final fallback to Groq LLM
#     print("[WARNING] All place APIs failed. Falling back to Groq LLM.")
#     try:
#         from rag_service import get_answer
#         return get_answer(question)
#     except Exception as e:
#         print(f"[ERROR] Final fallback to Groq failed: {e}")
#         return {"message": f"Sorry, I'm having trouble finding sightseeing suggestions for {city} right now."}



def nearby_agent(question, city="None", interests="None"):

    print("\n===================================")
    print("NEARBY AGENT CALLED")

    question = re.sub(r"\s+", " ", (question or "")).strip()

    print("QUESTION:", question)
    print("CITY:", city)
    print("===================================")

    # ---------------------------------
    # CHATGPT STYLE DISCOVERY MODE
    # ---------------------------------
    discover_mode = is_discover_query(question) and not any(
        kw in question.lower()
        for kw in ["plan a", "trip", "itinerary", "vacation", "holiday"]
    )

    print("DISCOVER QUERY:", discover_mode)

    if discover_mode:
        print("[DISCOVER] Running Discover Places Agent")

        result = discover_places(question)

        print(
            "[DISCOVER] Categories Found:",
            len(result.get("categories", []))
        )

        cats = ", ".join(
            c.get("label", "")
            for c in result.get("categories", [])
        )

        answer_text = (
            f"Here are the top places to explore in "
            f"{result.get('location','this destination')} "
            f"across {cats}."
        )

        if result.get("categories"):
            return {
                "source": "discover",
                "answer": answer_text,
                "nearbyResult": result
            }
        print("[DISCOVER] No categorized results; continuing through attraction fallbacks")

    # ---------------------------------
    # EXISTING FLOW
    # ---------------------------------

    if city == "None":
        return {
            "message":
            "I need to know which city you are visiting to suggest nearby places."
        }

    is_trip_plan = any(
        kw in question.lower()
        for kw in [
            "plan a",
            "trip",
            "itinerary",
            "vacation",
            "holiday"
        ]
    )

    # ---------------------------------
    # RAG CACHE
    # Skip RAG for discover queries
    # ---------------------------------
    if not is_trip_plan and not discover_mode:

        try:
            from rag_service import get_answer

            rag_result = get_answer(
                question,
                check_rag_only=True
            )

            if rag_result:
                print(
                    "[INFO] Found nearby place recommendations from RAG."
                )
                return rag_result

        except Exception as e:
            print(
                f"[WARNING] Error checking RAG: {e}"
            )

    # ---------------------------------
    # DISCOVER PLACES DYNAMIC CALL FOR TRIP PLANNING OR DISCOVERY
    # ---------------------------------
    print(f"[INFO] Invoking discover_places for city '{city}' with interests '{interests}' to fetch categorized attractions.")
    try:
        interest_text = "" if not interests or interests == "None" else f" for {interests}"
        disc_res = discover_places(f"tourist places in {city}{interest_text}")
        if disc_res and disc_res.get("categories"):
            # Flatten places for the 'data' field expected by calendar_agent
            flattened_data = []
            seen_names = set()
            for cat in disc_res["categories"]:
                for p in cat.get("places", []):
                    if p["name"] not in seen_names:
                        seen_names.add(p["name"])
                        flattened_data.append({
                            "attraction_id": p.get("id"),
                            "name": p.get("name"),
                            "rating": p.get("rating") if isinstance(p.get("rating"), (int, float)) else 4.2,
                            "reviews": p.get("ratingCount") or 0,
                            "address": p.get("address"),
                            "website": p.get("website") or "Not available",
                            "mapsUrl": p.get("mapsUrl"),
                            "wikiUrl": p.get("wikiUrl"),
                            "latitude": p.get("latitude"),
                            "longitude": p.get("longitude"),
                            "googlePhotoName": p.get("googlePhotoName"),
                            "image": p.get("image"),
                            "types": [cat.get("key"), "sightseeing"],
                            "categoryKey": cat.get("key"),
                            "categoryLabel": cat.get("label"),
                            "hours": p.get("hours") or [],
                            "editorial": p.get("description") or ""
                        })
            
            # Format categorized text response
            lines = []
            for cat in disc_res["categories"]:
                lines.append(f"\n### {cat.get('icon', '📍')} {cat.get('label')}\n")
                for i, p in enumerate(cat.get("places", [])[:5], 1):
                    item_lines = [f"**{p['name']}**"]
                    rating_val = p.get('rating')
                    reviews_val = p.get('ratingCount') or 0
                    rating_str = f"⭐ Rating: {rating_val}" if rating_val else "⭐ Rating: N/A"
                    if reviews_val:
                        rating_str += f" ({reviews_val} reviews)"
                    item_lines.append(rating_str)
                    item_lines.append(f"📍 Address: {p['address']}")
                    if p.get("description"):
                        item_lines.append(f"📝 {p['description']}")
                    lines.append(f"{i}. {chr(10).join(item_lines)}")
                    
            text_ans = f"Here are the top places to explore in {city.title()} by category:\n" + "\n".join(lines)
            
            return {
                "source": "discover_places",
                "answer": text_ans,
                "data": flattened_data,
                "nearbyResult": {
                    "location": city.title(),
                    "categories": disc_res["categories"]
                }
            }
    except Exception as e:
        print(f"[WARNING] Error running discover_places integration in nearby_agent: {e}")

    # ---------------------------------
    # GOOGLE PLACES
    # ---------------------------------
    print("[INFO] Checking Google Places API for attractions...")
    google_results = get_places_from_google(city, interests)
    if google_results:
        places_list = []
        for p in google_results["data"]:
                places_list.append({
                    "id": p.get("attraction_id"),
                    "name": p.get("name"),
                    "address": p.get("address"),
                    "rating": p.get("rating"),
                    "googlePhotoName": p.get("googlePhotoName"),
                    "image": None,
                    "description": p.get("editorial") or f"Explore {p.get('name')} in {city}."
                })
            
        nearby_res = {
            "location": city,
            "categories": [
                {
                    "label": "Attractions",
                    "places": places_list
                }
            ]
        }

        return {
            "source": "google_places",
            "answer": google_results["text"],
            "data": google_results["data"],
            "nearbyResult": nearby_res
        }

    try:
        from services.trip_service import get_structured_attractions
        llm_attractions = get_structured_attractions(city, "Moderate")
        if llm_attractions:
            return {
                "source": "llm_fallback",
                "answer": f"Top attractions in {city} generated after Google Places was unavailable.",
                "data": llm_attractions,
            }
    except Exception as e:
        print(f"[WARNING] LLM attraction fallback failed: {e}")

    # Fallback default structured attractions for city
    fallback_attractions = [
        {
            "id": f"fallback-attraction-1-{city}",
            "name": f"{city} Historic Temple & Heritage Quarter",
            "rating": 4.9,
            "reviews": 3200,
            "address": f"Old Heritage City, {city}",
            "category": "Culture",
            "latitude": 9.9195,
            "longitude": 78.1193,
            "description": f"Iconic ancient landmark and cultural heart of {city}."
        },
        {
            "id": f"fallback-attraction-2-{city}",
            "name": f"{city} Royal Palace & Museum",
            "rating": 4.7,
            "reviews": 1800,
            "address": f"Palace Road, {city}",
            "category": "History",
            "latitude": 9.9160,
            "longitude": 78.1230,
            "description": f"Architectural masterpiece with giant pillars and light show in {city}."
        }
    ]
    return {"source": "fallback", "answer": f"Top attractions in {city}", "data": fallback_attractions}
