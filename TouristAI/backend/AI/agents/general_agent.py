from rag_service import get_answer, save_to_rag
import os
import urllib.request
import urllib.error
import urllib.parse
import json
import base64
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

import base64
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote



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

def general_agent(state):
    """
    Flow:
    1. Check RAG
    2. Check Google Places
    3. Call Groq
    """

    question = state.get("question")
    city = state.get("city", "None")
    budget = state.get("budget", "None")
    travelers = state.get("travelers", 1)


    # ------------------------------------
    # 1. Check RAG
    # ------------------------------------
    print("Checking RAG...")

    rag_result = get_answer(
        question,
        check_rag_only=True
    )

    if rag_result:
        print("Answer from RAG")
        return rag_result

    # ------------------------------------
    # 2. Check Google Places
    # ------------------------------------
    print("Checking Google Places...")

    google_result = search_google_places(question, city, budget, travelers)

    if google_result:

        save_to_rag(
            question,
            google_result
        )

        return {
            "source": "Google Places",
            "answer": google_result
        }

    # ------------------------------------
    # 3. Call Groq
    # ------------------------------------
    print("Calling Groq...")

    groq_result = get_answer(
        question,
        check_rag_only=False
    )

    return groq_result

def search_google_places(question: str, city: str, budget: str, travelers: int) -> str | None:
    import os
    import json
    import urllib.request
    import urllib.error
    import urllib.parse

    api_key = os.getenv("GOOGLE_PLACES_API_KEY")

    if not api_key:
        print("GOOGLE_PLACES_API_KEY not found")
        return None

    query = question

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

    try:

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode())

        print(json.dumps(data, indent=2))

        if not data.get("places"):
            return None

        lines = []

        PRICE_LEVEL = {
            "PRICE_LEVEL_FREE": "Free",
            "PRICE_LEVEL_INEXPENSIVE": "₹",
            "PRICE_LEVEL_MODERATE": "₹₹",
            "PRICE_LEVEL_EXPENSIVE": "₹₹₹",
            "PRICE_LEVEL_VERY_EXPENSIVE": "₹₹₹₹"
        }

        for i, place in enumerate(data["places"], 1):

            name = place.get("displayName", {}).get("text", "N/A")
            rating = place.get("rating", "N/A")
            reviews = place.get("userRatingCount", 0)
            address = place.get("formattedAddress", "N/A")
            website = place.get("websiteUri")
            google_map = place.get("googleMapsUri")
            phone = place.get("nationalPhoneNumber")
            intl_phone = place.get("internationalPhoneNumber")
            status = place.get("businessStatus")
            primary_type = place.get("primaryType")
            types = ", ".join(place.get("types", []))

            latitude = place.get("location", {}).get("latitude")
            longitude = place.get("location", {}).get("longitude")

            price = PRICE_LEVEL.get(
                place.get("priceLevel", ""),
                place.get("priceLevel", "")
            )

            summary = place.get("editorialSummary", {}).get("text")

            hours = (
                place.get("currentOpeningHours", {}).get("weekdayDescriptions")
                or place.get("regularOpeningHours", {}).get("weekdayDescriptions")
                or []
            )

            # --------------------------
            # Website Images
            # --------------------------

            photo_urls = []

            if website:
                photo_urls = get_image_from_website(
                    website,
                    max_images=1
                )

            item_lines = []

            item_lines.append(f"**{name}**")

            item_lines.append(
                f"⭐ Rating: {rating} ({reviews} reviews)"
            )

            if price:
                item_lines.append(f"💰 Price Level: {price}")

            item_lines.append(f"📍 Address: {address}")

            # if latitude and longitude:
            #     item_lines.append(
            #         f"🌎 Coordinates: {latitude}, {longitude}"
            #     )

            if primary_type:
                item_lines.append(
                    f"🏨 Primary Type: {primary_type}"
                )

            if types:
                item_lines.append(
                    f"📂 Types: {types}"
                )

            if status:
                item_lines.append(
                    f"🟢 Business Status: {status}"
                )

            if phone:
                item_lines.append(
                    f"☎ National Phone: {phone}"
                )

            if intl_phone:
                item_lines.append(
                    f"🌍 International Phone: {intl_phone}"
                )

            if summary:
                item_lines.append(
                    f"📝 {summary}"
                )

            if hours:
                item_lines.append("🕒 Hours:")
                for h in hours:
                    item_lines.append(f"🕒 {h}")

            # ---------- Features ----------

            if place.get("goodForChildren"):
                item_lines.append("👨‍👩‍👧 Good for Children")

            if place.get("goodForGroups"):
                item_lines.append("👥 Good for Groups")

            if place.get("allowsDogs"):
                item_lines.append("🐶 Dogs Allowed")

            if place.get("servesBreakfast"):
                item_lines.append("🍳 Breakfast Available")

            if place.get("servesLunch"):
                item_lines.append("🥗 Lunch Available")

            if place.get("servesDinner"):
                item_lines.append("🍽 Dinner Available")

            if place.get("servesBeer"):
                item_lines.append("🍺 Beer Available")

            if place.get("servesWine"):
                item_lines.append("🍷 Wine Available")

            if place.get("servesVegetarianFood"):
                item_lines.append("🥦 Vegetarian Food Available")

            if place.get("takeout"):
                item_lines.append("🥡 Takeout Available")

            if place.get("delivery"):
                item_lines.append("🚚 Delivery Available")

            if place.get("dineIn"):
                item_lines.append("🍴 Dine-in Available")

            # ---------- Payment Options ----------

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

            # ---------- Parking ----------

            parking = place.get("parkingOptions", {})

            if parking:
                parking_info = [k.replace('parking', '').replace('free', 'Free ').replace('paid', 'Paid ').strip() for k, v in parking.items() if v]
                if parking_info:
                    item_lines.append(f"🅿 Parking: {', '.join(parking_info)}")

            # ---------- Accessibility ----------

            access = place.get("accessibilityOptions", {})

            access_info = [
                "wheelchair accessible parking" for k, v in access.items() if k == "wheelchairAccessibleParking" and v
            ] + [
                "wheelchair accessible entrance" for k, v in access.items() if k == "wheelchairAccessibleEntrance" and v
            ]
            if access_info:
                item_lines.append(f"♿ {', '.join(access_info).capitalize()}")

            # ---------- Links ----------

            if google_map:
                item_lines.append(f"[View Map]({google_map})")

            elif address != "N/A":
                map_url = (
                    "https://www.google.com/maps/search/?api=1&query="
                    + urllib.parse.quote_plus(address)
                )
                item_lines.append(f"[View Map]({map_url})")

            if website:
                item_lines.append(
                    f"[Visit Website]({website})"
                )

            # ---------- Images ----------

            for photo in photo_urls:
                item_lines.append(
                    f"![{name}]({photo})"
                )

            lines.append(
                f"{i}. " + "\n".join(item_lines)
            )

        return "\n".join(lines)

    except urllib.error.HTTPError as e:
        print(e.read().decode())
        return None

    except Exception as e:
        print(e)
        return None
        