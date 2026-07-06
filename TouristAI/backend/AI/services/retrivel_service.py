from database.postgres import get_connection


class RetrievalService:

    @staticmethod
    def search_discover(city):

        conn = get_connection()
        cursor = conn.cursor()

        try:

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

            # Fetch attractions

            cursor.execute("""
                SELECT
                    attraction_name,
                    category,
                    popularity_level,
                    risk_level,
                    family_friendly,
                    best_visit_time,
                    visit_duration
                FROM attraction_details
                WHERE destination_id=%s
                ORDER BY attraction_name
            """, (destination_id,))

            rows = cursor.fetchall()

            result = {

                "popular": [],
                "medium": [],
                "hidden": []

            }

            for row in rows:

                attraction = {

                    "name": row[0],
                    "category": row[1],
                    "risk": row[3],
                    "family": row[4],
                    "best_time": row[5],
                    "duration": row[6]

                }

                popularity = (row[2] or "").lower()

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