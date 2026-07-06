import requests
import time

from database.postgres import get_connection

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"


def search_wikipedia(query):
    """
    Search Wikipedia and return the best matching page title.
    """

    try:
        response = requests.get(
            WIKIPEDIA_API,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json"
            },
            timeout=10
        )

        data = response.json()

        results = data["query"]["search"]

        if results:
            return results[0]["title"]

    except Exception as e:
        print("Search Error:", e)

    return None


def get_page_image(title):
    """
    Get image from a Wikipedia page title.
    """

    try:
        response = requests.get(
            WIKIPEDIA_API,
            params={
                "action": "query",
                "titles": title,
                "prop": "pageimages",
                "format": "json",
                "pithumbsize": 1000
            },
            timeout=10
        )

        data = response.json()

        pages = data["query"]["pages"]

        for page in pages.values():

            if "thumbnail" in page:
                return page["thumbnail"]["source"]

    except Exception as e:
        print("Image Error:", e)

    return None


def get_wikipedia_image(attraction_name, destination_name):

    # Try attraction + destination
    search_query = f"{attraction_name} {destination_name}"

    title = search_wikipedia(search_query)

    if title:
        print(f"Found title: {title}")

        image = get_page_image(title)

        if image:
            return image

    # Try attraction only
    title = search_wikipedia(attraction_name)

    if title:
        print(f"Fallback title: {title}")

        image = get_page_image(title)

        if image:
            return image

    # Try destination only
    title = search_wikipedia(destination_name)

    if title:
        print(f"Destination title: {title}")

        image = get_page_image(title)

        if image:
            return image

    return None


def load_images():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            a.id,
            a.attraction_name,
            d.destination_name
        FROM attraction_details a
        JOIN destinations d
        ON a.destination_id = d.id
    """)

    rows = cursor.fetchall()

    print(f"\nFound {len(rows)} attractions\n")

    for attraction_id, attraction_name, destination_name in rows:

        print("\n--------------------------------")
        print("Attraction:", attraction_name)
        print("Destination:", destination_name)

        image_url = get_wikipedia_image(
            attraction_name,
            destination_name
        )

        if image_url:

            cursor.execute("""
                UPDATE attraction_details
                SET imageurl = %s
                WHERE id = %s
            """,
            (
                image_url,
                attraction_id
            ))

            conn.commit()

            print("✓ Saved")
            print(image_url)

        else:

            print("✗ No image found")

        time.sleep(1)

    cursor.close()
    conn.close()

    print("\nCompleted image loading.")


if __name__ == "__main__":
    load_images()