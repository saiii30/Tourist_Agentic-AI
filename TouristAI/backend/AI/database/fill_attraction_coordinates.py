import time
from geopy.geocoders import Nominatim
from postgres import get_connection

geolocator = Nominatim(user_agent="tourist_ai")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
SELECT
id,
attraction_name,
destination_id
FROM attraction_details
WHERE latitude IS NULL
""")

rows = cursor.fetchall()

for attraction_id, attraction_name, destination_id in rows:

    cursor.execute("""
    SELECT destination_name,state
    FROM destinations
    WHERE id=%s
    """,(destination_id,))

    destination = cursor.fetchone()

    if not destination:
        continue

    city,state = destination

    try:

        query = f"{attraction_name}, {city}, {state}, India"

        location = geolocator.geocode(query)

        if location:

            print(query)

            cursor.execute("""
                UPDATE attraction_details
                SET latitude=%s,
                    longitude=%s
                WHERE id=%s
            """,
            (
                location.latitude,
                location.longitude,
                attraction_id
            ))

            conn.commit()

        else:
            print(query, "Not Found")

    except Exception as e:
        print(query, e)

    time.sleep(1)

cursor.close()
conn.close()