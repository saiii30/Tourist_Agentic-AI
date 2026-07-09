import os
import json
import re
import urllib.request
import urllib.error
import urllib.parse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


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

def search_hotel_url(hotel_name, city, site):
    query = f"{hotel_name} {city} site:{site}"

    url = f"https://www.google.com/search?q={quote_plus(query)}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        soup = BeautifulSoup(response.text, "html.parser")

        for a in soup.select("a"):

            href = a.get("href")

            if not href:
                continue

            if "/url?q=" not in href:
                continue

            real_url = href.split("/url?q=")[1].split("&")[0]

            if site in real_url:
                return real_url

    except Exception as e:
        print(e)

    return None


def generate_ota_links(hotel_name: str, city: str, checkin=None, checkout=None, adults=1, rooms=1):
    """
    Builds real, working URLs for major OTAs (Booking.com, Agoda,
    MakeMyTrip) — landing on each OTA's own city hotel-listing page,
    not a Google search tab.

    How each one actually works:
    - Booking.com: public search box genuinely accepts a free-text
      "ss" parameter (plus checkin/checkout/group_adults/no_rooms),
      so this lands directly on real filtered results.
    - Agoda: does NOT accept free-text city names in its search API
      URLs (those need an internal numeric city ID we don't have).
      BUT Agoda separately publishes SEO-friendly city landing pages
      at a fixed, documented pattern:
          https://www.agoda.com/city/{city-slug}-in.html
      (confirmed working for bangalore, hyderabad, chennai, etc.)
      This lists real hotels for that city on agoda.com itself.
    - MakeMyTrip: same story — the search API needs an internal
      city code (e.g. CTMAA for Chennai), which we don't have. But
      MakeMyTrip also publishes SEO city-listing pages at:
          https://www.makemytrip.com/hotels/{city-slug}-hotels.html
      (confirmed working for madurai, salem, etc.)

    Both SEO patterns only take a *city*, not a specific hotel name —
    Agoda/MakeMyTrip don't expose a working hotel-name deep link
    without their affiliate ID lookup. So these two links land the
    user on the right city's hotel list on the OTA's own site, where
    they can find the specific property themselves. Booking.com's
    link is the only one of the three that's hotel-name-specific.
    """

    search_text = f"{hotel_name} {city}".strip() if hotel_name else city
    city_slug = re.sub(r"[^a-z0-9]+", "-", city.strip().lower()).strip("-")

    links = {}

    # -----------------------
    # Booking.com — real deep link (genuine free-text param, hotel-specific)
    # -----------------------
    booking_params = {
        "ss": search_text,
        "group_adults": adults,
        "no_rooms": rooms,
    }
    if checkin:
        booking_params["checkin"] = checkin
    if checkout:
        booking_params["checkout"] = checkout
    links["booking_com"] = (
        "https://www.booking.com/searchresults.html?"
        + urllib.parse.urlencode(booking_params)
    )

        # Agoda
    agoda = search_hotel_url(hotel_name, city, "agoda.com")

    if agoda:
        links["agoda"] = agoda
    else:
        links["agoda"] = f"https://www.agoda.com/city/{city_slug}-in.html"


    # MakeMyTrip
    mmt = search_hotel_url(hotel_name, city, "makemytrip.com")

    if mmt:
        links["makemytrip"] = mmt
    else:
        links["makemytrip"] = f"https://www.makemytrip.com/hotels/{city_slug}-hotels.html"


    # Goibibo
    goibibo = search_hotel_url(hotel_name, city, "goibibo.com")

    if goibibo:
        links["goibibo"] = goibibo
    else:
        links["goibibo"] = f"https://www.goibibo.com/hotels/hotels-in-{city_slug}-ct/"


    # Cleartrip
    cleartrip = search_hotel_url(hotel_name, city, "cleartrip.com")

    if cleartrip:
        links["cleartrip"] = cleartrip
    else:
        links["cleartrip"] = f"https://www.cleartrip.com/hotels/{city_slug}"

    return links


def get_room_details_from_website(url):
    """
    Attempts to extract structured hotel/room data (number of rooms,
    room types, amenities, parking) from a hotel's own website.

    Looks for schema.org JSON-LD (LodgingBusiness / Hotel) first,
    then falls back to keyword scanning of visible text.

    Returns a dict. Any field not found is left as None so the caller
    can clearly report "not available" instead of guessing.
    """

    result = {
        "number_of_rooms": None,
        "room_types": [],
        "amenities": [],
        "parking": None,
        "source": None,
    }

    if not url or url == "Not available":
        return result

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0 Safari/537.36"
            )
        }

        response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # -----------------------
        # 1. Try JSON-LD (schema.org) first — this is the only
        #    semi-reliable structured source most hotel sites expose.
        # -----------------------
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "{}")
            except (json.JSONDecodeError, TypeError):
                continue

            candidates = data if isinstance(data, list) else [data]

            for entry in candidates:
                if not isinstance(entry, dict):
                    continue

                entry_type = entry.get("@type", "")
                type_str = entry_type if isinstance(entry_type, str) else " ".join(entry_type)

                if "Hotel" in type_str or "LodgingBusiness" in type_str:
                    if entry.get("numberOfRooms"):
                        nr = entry["numberOfRooms"]
                        if isinstance(nr, dict):
                            result["number_of_rooms"] = nr.get("value")
                        else:
                            result["number_of_rooms"] = nr

                    amenities = entry.get("amenityFeature", [])
                    for a in amenities:
                        if isinstance(a, dict) and a.get("name"):
                            result["amenities"].append(a["name"])

                    if entry.get("petsAllowed") is not None:
                        result["amenities"].append(
                            "Pets allowed" if entry["petsAllowed"] else "No pets"
                        )

                    result["source"] = "json-ld"

        # -----------------------
        # 2. Keyword scan fallback for parking + room type hints
        #    (best-effort only — not guaranteed accurate)
        # -----------------------
        text = soup.get_text(" ", strip=True).lower()

        if result["parking"] is None:
            if "free parking" in text:
                result["parking"] = "Free parking (mentioned on site)"
            elif "paid parking" in text or "valet parking" in text:
                result["parking"] = "Paid/valet parking (mentioned on site)"
            elif "parking" in text:
                result["parking"] = "Parking mentioned (details unclear)"

        room_keywords = {
            "single room": "Single Room",
            "double room": "Double Room",
            "twin room": "Twin Room",
            "deluxe room": "Deluxe Room",
            "suite": "Suite",
            "family room": "Family Room",
            "executive room": "Executive Room",
        }

        for kw, label in room_keywords.items():
            if kw in text and label not in result["room_types"]:
                result["room_types"].append(label)

        if not result["source"] and (result["room_types"] or result["parking"]):
            result["source"] = "text-scan"

        return result

    except Exception as e:
        print("Room detail scrape error:", e)
        return result


def get_hotels_from_google(city: str, budget: str, travelers: int, checkin=None, checkout=None, rooms=1) -> str | None:
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
        "places.photos,"
        "places.regularOpeningHours,"
        "places.currentOpeningHours,"
        "places.parkingOptions"
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

        print(json.dumps(data, indent=2))

        if not data.get("places"):
            print("⚠️ No hotels found.")
            return None

        lines = []

        for i, place in enumerate(data["places"][:10], 1):
            print(place)
            name = place.get("displayName", {}).get("text", "N/A")
            rating = place.get("rating", "N/A")
            reviews = place.get("userRatingCount", 0)
            address = place.get("formattedAddress", "Address not available")
            website = place.get("websiteUri", "Not available")

            # -----------------------
            # Opening / closing hours
            # -----------------------
            # -----------------------
            # Parking (from Google, when Google has it)
            # -----------------------
            google_parking = place.get("parkingOptions", {})
            google_parking_flags = [k for k, v in google_parking.items() if v]
            google_parking_text = ", ".join(google_parking_flags) if google_parking_flags else None

            # -----------------------
            # Images
            # -----------------------
            photo_urls = []
            if website != "Not available":
                print(f"Getting images from: {website}")
                photo_urls = get_image_from_website(website, max_images=20)
                print("Images:", photo_urls)

            # -----------------------
            # Room details (best-effort, from hotel's own site)
            # -----------------------
            room_details = get_room_details_from_website(website)

            item_lines = [f"**{name}**"]
            item_lines.append(f"⭐ Rating: {rating} ({reviews} reviews)")
            item_lines.append(f"📍 Address: {address}")

            hours = (
                place.get("currentOpeningHours", {}).get("weekdayDescriptions")
                or place.get("regularOpeningHours", {}).get("weekdayDescriptions")
                or []
            )
            if hours:
                for h in hours:
                    item_lines.append(f"🕒 {h}")

            # Parking: prefer Google's structured flag, else scraped mention
            if google_parking_text:
                item_lines.append(f"🅿️ Parking: {google_parking_text}")
            elif room_details["parking"]:
                item_lines.append(f"🅿️ Parking: {room_details['parking']}")
            else:
                item_lines.append("🅿️ Parking: Not specified")

            # Room count
            if room_details["number_of_rooms"]:
                item_lines.append(f"🛏️ Total Rooms: {room_details['number_of_rooms']}")
            else:
                item_lines.append("🛏️ Total Rooms: Not available (not published by hotel)")

            # Room types (single/double/etc.) — best effort only
            if room_details["room_types"]:
                item_lines.append(f"🛌 Room Types Mentioned: {', '.join(room_details['room_types'])}")
            else:
                item_lines.append("🛌 Room Types: Not specified on hotel website")

            if room_details["amenities"]:
                item_lines.append(f"✨ Amenities: {', '.join(room_details['amenities'][:10])}")

            if address != "Address not available":
                map_query = urllib.parse.quote_plus(address)
                map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
                item_lines.append(f"[View Map]({map_url})")

            if website != "Not available":
                item_lines.append(f"[Visit Website]({website})")

            # -----------------------
            # OTA deep links (Booking.com / Agoda / MakeMyTrip)
            # -----------------------
            ota_links = generate_ota_links(
                hotel_name=name,
                city=city,
                checkin=checkin,
                checkout=checkout,
                adults=travelers,
                rooms=rooms,
            )
            item_lines.append(
                f"🔎 Compare prices: "
                f"[Booking.com]({ota_links['booking_com']}) | "
                f"[Agoda]({ota_links['agoda']}) | "
                f"[MakeMyTrip]({ota_links['makemytrip']}) | "
                f"[Goibibo]({ota_links['goibibo']}) | "
                f"[Cleartrip]({ota_links['cleartrip']})"
            )

            if photo_urls:
                for photo in photo_urls:
                    item_lines.append(f"![{name}]({photo})")

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


def hotel_agent(question, city="None", budget="None", travelers=1, checkin=None, checkout=None, rooms=1):
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
        city, budget, travelers, checkin=checkin, checkout=checkout, rooms=rooms
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