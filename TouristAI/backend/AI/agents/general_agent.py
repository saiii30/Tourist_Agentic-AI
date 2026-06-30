from rag_service import get_answer, save_to_rag


def general_agent(question):
    """
    Flow:
    1. Check RAG
    2. Check Google Places
    3. Call Groq
    """

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

    google_result = search_google_places(question)

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

def search_google_places(query: str):
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")

    if not api_key:
        return None

    url = "https://places.googleapis.com/v1/places:searchText"

    field_mask = (
        "places.displayName,"
        "places.formattedAddress,"
        "places.rating,"
        "places.userRatingCount,"
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

        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))

        if not data.get("places"):
            return None

        lines = []

        for place in data["places"]:
            name = place.get("displayName", {}).get("text", "N/A")
            address = place.get("formattedAddress", "N/A")
            rating = place.get("rating", "N/A")
            reviews = place.get("userRatingCount", 0)
            website = place.get("websiteUri", "N/A")

            lines.append(f"📍 {name}")
            lines.append(f"⭐ Rating: {rating} ({reviews} reviews)")
            lines.append(f"🏠 Address: {address}")

            if website != "N/A":
                lines.append(f"🌐 Website: {website}")

            photos = place.get("photos")
            if photos:
                photo = get_place_photo(
                    photos[0]["name"],
                    api_key
                )

                if photo:
                    lines.append(f"🖼️ Photo: {photo}")

            lines.append("")

        return "\n".join(lines)

    except Exception as e:
        print(e)
        return None