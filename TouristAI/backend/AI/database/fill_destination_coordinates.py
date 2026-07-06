import time
from geopy.geocoders import Nominatim
from postgres import get_connection

geolocator = Nominatim(user_agent="tourist_ai")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
SELECT id, destination_name, state
FROM destinations
WHERE latitude IS NULL
""")

rows = cursor.fetchall()

for destination_id, city, state in rows:

    try:
        location = geolocator.geocode(f"{city}, {state}, India")

        if location:

            print(city, location.latitude, location.longitude)

            cursor.execute("""
                UPDATE destinations
                SET latitude=%s,
                    longitude=%s
                WHERE id=%s
            """,
            (
                location.latitude,
                location.longitude,
                destination_id
            ))

            conn.commit()

        else:
            print(city, "Not Found")

    except Exception as e:
        print(city, e)

    time.sleep(1)   # Be polite to the free service

cursor.close()
conn.close()