from database.postgres import get_connection
from utils.query_parser import resolve_destination

def get_discover_places(city):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        print(f"Searching attractions for {city}")
        # Find destination
        cursor.execute("""
            SELECT id
            FROM destinations
            WHERE LOWER(destination_name)=LOWER(%s)
               OR LOWER(state)=LOWER(%s)
            LIMIT 1
        """, (city, city))

        destination = cursor.fetchone()

        if not destination:
            return None

        destination_id = destination[0]

        # Fetch all attraction information
        cursor.execute("""
            SELECT
                attraction_name,
                category,
                description,
                popularity_level,
                risk_level,
                family_friendly,
                best_visit_time,
                visit_duration,
                latitude,
                longitude
            FROM attraction_details
            WHERE destination_id=%s
            ORDER BY popularity_level DESC,
                     attraction_name
        """, (destination_id,))

        rows = cursor.fetchall()

        result = {
            "city": city,
            "popular": [],
            "medium": [],
            "hidden": []
        }

        for row in rows:

            attraction = {

                "name": row[0],
                "category": row[1],
                "description": row[2],
                "popularity": row[3],
                "risk": row[4],
                "family": row[5],
                "best_time": row[6],
                "duration": row[7],
                "latitude": row[8],
                "longitude": row[9]

            }

            popularity = (row[3] or "").lower()

            if popularity == "popular":

                result["popular"].append(attraction)

            elif popularity == "medium":

                result["medium"].append(attraction)

            else:

                result["hidden"].append(attraction)

        return result

    finally:

        cursor.close()
        conn.close()


