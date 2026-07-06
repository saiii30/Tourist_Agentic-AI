from database.postgres import get_connection
import math
import json


class NearbyService:

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):

        R = 6371

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2)
            * math.sin(dlat / 2)
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2)
            * math.sin(dlon / 2)
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    @staticmethod
    def get_nearby_places(city, radius=180):

        conn = get_connection()
        cursor = conn.cursor()

        try:

            #####################################################
            # Source Destination
            #####################################################

            cursor.execute("""
                SELECT
                    latitude,
                    longitude
                FROM destinations
                WHERE LOWER(destination_name)=LOWER(%s)
                LIMIT 1
            """, (city,))

            source = cursor.fetchone()

            if not source:
                return []

            source_lat = source[0]
            source_lon = source[1]

            if source_lat is None or source_lon is None:
                return []

            #####################################################
            # Fetch all destinations
            #####################################################

            cursor.execute("""
                SELECT

                    destination_name,
                    state,
                    region,
                    activities_available,
                    trip_types,
                    ideal_days,
                    popularity_score,
                    safety_rating,
                    latitude,
                    longitude

                FROM destinations
            """)

            nearby = []

            for row in cursor.fetchall():

                destination_name = row[0]

                if destination_name.lower() == city.lower():
                    continue

                lat = row[8]
                lon = row[9]

                if lat is None or lon is None:
                    continue

                distance = NearbyService.haversine(

                    source_lat,
                    source_lon,
                    lat,
                    lon

                )

                if distance <= radius:

                    activities = row[3]
                    trip_types = row[4]

                    if isinstance(activities, str):
                        try:
                            activities = json.loads(activities)
                        except:
                            activities = []

                    if isinstance(trip_types, str):
                        try:
                            trip_types = json.loads(trip_types)
                        except:
                            trip_types = []

                    nearby.append({

                        "name": destination_name,

                        "state": row[1],

                        "region": row[2],

                        "distance": round(distance),

                        "activities": activities,

                        "trip_types": trip_types,

                        "ideal_days": row[5],

                        "popularity_score": row[6],

                        "safety_rating": row[7]

                    })

            nearby.sort(key=lambda x: x["distance"])

            return nearby[:5]

        finally:

            cursor.close()
            conn.close()