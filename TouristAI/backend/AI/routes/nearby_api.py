# from fastapi import APIRouter
# from database.postgres import get_connection
# import math

# router = APIRouter(prefix="/api")


# def haversine(lat1, lon1, lat2, lon2):
#     R = 6371

#     dLat = math.radians(lat2 - lat1)
#     dLon = math.radians(lon2 - lon1)

#     a = (
#         math.sin(dLat / 2) ** 2
#         + math.cos(math.radians(lat1))
#         * math.cos(math.radians(lat2))
#         * math.sin(dLon / 2) ** 2
#     )

#     return R * 2 * math.asin(math.sqrt(a))


# @router.get("/nearby")
# def nearby(lat: float, lon: float):

#     conn = get_connection()
#     cur = conn.cursor()

#     cur.execute("""
#         SELECT
#             attraction_name,
#             description,
#             latitude,
#             longitude,
#             category
#         FROM attraction_details
#         WHERE latitude IS NOT NULL
#         AND longitude IS NOT NULL
#     """)

#     rows = cur.fetchall()

#     cur.close()
#     conn.close()

#     result = []

#     for row in rows:

#         dist = haversine(
#             lat,
#             lon,
#             float(row[2]),
#             float(row[3])
#         )

#         result.append({
#             "name": row[0],
#             "history": row[1],
#             "lat": float(row[2]),
#             "lon": float(row[3]),
#             "category": row[4],
#             "distance": round(dist,2)
#         })

#     result.sort(key=lambda x: x["distance"])

#     return result[:30]

# from fastapi import APIRouter
# import requests
# import os

# router = APIRouter(prefix="/api")

# # Store your API key as an environment variable:
# # GOOGLE_API_KEY=xxxxxxxxxxxxxxxx
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# # For testing only (remove after testing)
# # GOOGLE_API_KEY = "YOUR_NEW_API_KEY"


# @router.get("/nearby")
# def nearby(lat: float, lon: float):

#     url = "https://places.googleapis.com/v1/places:searchNearby"

#     headers = {
#         "Content-Type": "application/json",
#         "X-Goog-Api-Key": GOOGLE_API_KEY,
#         "X-Goog-FieldMask":
#             "places.displayName,"
#             "places.location,"
#             "places.types,"
#             "places.rating,"
#             "places.formattedAddress"
#     }

#     body = {
#         "includedTypes": [
#             "tourist_attraction",
#             "restaurant",
#             "cafe",
#             "shopping_mall",
#             "store",
#             "supermarket",
#             "atm",
#             "bank",
#             "hospital",
#             "pharmacy",
#             "parking",
#             "bus_station",
#             "lodging",
#             "museum"
#         ],
#         "maxResultCount": 30,
#         "locationRestriction": {
#             "circle": {
#                 "center": {
#                     "latitude": lat,
#                     "longitude": lon
#                 },
#                 "radius": 500.0
#             }
#         }
#     }

#     try:

#         response = requests.post(
#             url,
#             headers=headers,
#             json=body,
#             timeout=20
#         )

#         print("Status:", response.status_code)
#         print(response.text)

#         if response.status_code != 200:
#             return {
#                 "error": "Google Places API Error",
#                 "status": response.status_code,
#                 "details": response.text
#             }

#         data = response.json()

#         places = []

#         for place in data.get("places", []):

#             types = place.get("types", [])

#             category = "📍 Nearby"

#             if "shopping_mall" in types:
#                 category = "🛍 Shopping"

#             elif "store" in types:
#                 category = "🛍 Shopping"

#             elif "supermarket" in types:
#                 category = "🛒 Supermarket"

#             elif "restaurant" in types:
#                 category = "🍽 Restaurant"

#             elif "cafe" in types:
#                 category = "☕ Cafe"

#             elif "bakery" in types:
#                 category = "🥤 Famous Food"

#             elif "tourist_attraction" in types:
#                 category = "📸 Tourist Spot"

#             elif "museum" in types:
#                 category = "🏛 Museum"

#             elif "hospital" in types:
#                 category = "🏥 Hospital"

#             elif "atm" in types:
#                 category = "💳 ATM"

#             elif "bank" in types:
#                 category = "🏦 Bank"

#             elif "bus_station" in types:
#                 category = "🚌 Bus Stop"

#             elif "parking" in types:
#                 category = "🅿 Parking"

#             elif "lodging" in types:
#                 category = "🏨 Hotel"

#             elif "pharmacy" in types:
#                 category = "💊 Pharmacy"

#             places.append({
#                 "name": place["displayName"]["text"],
#                 "lat": place["location"]["latitude"],
#                 "lon": place["location"]["longitude"],
#                 "rating": place.get("rating", 0),
#                 "category": category,
#                 "address": place.get("formattedAddress", ""),
#                 "types": types
#             })

#         return places

#     except Exception as e:
#         return {
#             "error": str(e)
#         }


from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/nearby")
def nearby(lat: float, lon: float):

    # =========================
    # Meenakshi Amman Temple
    # 9.91906, 78.1188
    # =========================
    if (
        abs(lat - 9.91906) < 0.02
        and abs(lon - 78.1188) < 0.02
    ):
        return [
            {
                "name": "Puthu Mandapam",
                "lat": 9.9189,
                "lon": 78.1191,
                "rating": 4.6,
                "category": "🛍 Shopping",
                "address": "150 m"
            },
            {
                "name": "Famous Jigarthanda",
                "lat": 9.9201,
                "lon": 78.1177,
                "rating": 4.8,
                "category": "🥤 Famous Food",
                "address": "220 m"
            },
            {
                "name": "East Tower View Point",
                "lat": 9.9193,
                "lon": 78.1194,
                "rating": 4.7,
                "category": "📸 Tourist Spot",
                "address": "90 m"
            },
            {
                "name": "Public Toilet",
                "lat": 9.9188,
                "lon": 78.1182,
                "rating": 4.0,
                "category": "🚻 Public Toilet",
                "address": "60 m"
            },
            {
                "name": "Indian Bank ATM",
                "lat": 9.9194,
                "lon": 78.1184,
                "rating": 4.2,
                "category": "💳 ATM",
                "address": "35 m"
            },
            {
                "name": "Auto Stand",
                "lat": 9.9198,
                "lon": 78.1181,
                "rating": 4.1,
                "category": "🚕 Auto Stand",
                "address": "45 m"
            },
            {
                "name": "Government Hospital",
                "lat": 9.9207,
                "lon": 78.1202,
                "rating": 4.3,
                "category": "🏥 Hospital",
                "address": "250 m"
            }
        ]

    # =========================
    # Jaipur Palace / Hawa Mahal
    # 26.9258,75.8237
    # =========================
    elif (
        abs(lat - 26.9258) < 0.02
        and abs(lon - 75.8237) < 0.02
    ):
        return [
            {
                "name": "Johari Bazaar",
                "lat": 26.9252,
                "lon": 75.8241,
                "rating": 4.7,
                "category": "🛍 Shopping",
                "address": "120 m"
            },
            {
                "name": "LMB Restaurant",
                "lat": 26.9249,
                "lon": 75.8235,
                "rating": 4.6,
                "category": "🍽 Restaurant",
                "address": "180 m"
            },
            {
                "name": "Photo Point",
                "lat": 26.9255,
                "lon": 75.8248,
                "rating": 4.8,
                "category": "📸 Tourist Spot",
                "address": "60 m"
            },
            {
                "name": "ATM",
                "lat": 26.9260,
                "lon": 75.8228,
                "rating": 4.2,
                "category": "💳 ATM",
                "address": "40 m"
            },
            {
                "name": "Public Toilet",
                "lat": 26.9256,
                "lon": 75.8232,
                "rating": 4.0,
                "category": "🚻 Public Toilet",
                "address": "75 m"
            },
            {
                "name": "Taxi Stand",
                "lat": 26.9251,
                "lon": 75.8230,
                "rating": 4.1,
                "category": "🚕 Taxi",
                "address": "55 m"
            }
        ]

    # =========================
    # Srirangam Temple
    # 10.8600,78.6900
    # =========================
    elif (
        abs(lat - 10.8600) < 0.02
        and abs(lon - 78.6900) < 0.02
    ):
        return [
            {
                "name": "Chithirai Street Shops",
                "lat": 10.8602,
                "lon": 78.6908,
                "rating": 4.5,
                "category": "🛍 Shopping",
                "address": "100 m"
            },
            {
                "name": "Temple Prasadam Center",
                "lat": 10.8605,
                "lon": 78.6895,
                "rating": 4.8,
                "category": "🥤 Famous Food",
                "address": "70 m"
            },
            {
                "name": "Rajagopuram View Point",
                "lat": 10.8598,
                "lon": 78.6909,
                "rating": 4.9,
                "category": "📸 Tourist Spot",
                "address": "40 m"
            },
            {
                "name": "ATM",
                "lat": 10.8604,
                "lon": 78.6899,
                "rating": 4.2,
                "category": "💳 ATM",
                "address": "30 m"
            },
            {
                "name": "Auto Stand",
                "lat": 10.8599,
                "lon": 78.6892,
                "rating": 4.1,
                "category": "🚕 Auto Stand",
                "address": "50 m"
            }
        ]

    # =========================
    # Bangalore Palace
    # 12.9977,77.5927
    # =========================
    elif (
        abs(lat - 12.9977) < 0.02
        and abs(lon - 77.5927) < 0.02
    ):
        return [
            {
                "name": "Sadashiv Nagar Market",
                "lat": 12.9980,
                "lon": 77.5931,
                "rating": 4.5,
                "category": "🛍 Shopping",
                "address": "150 m"
            },
            {
                "name": "CTR Benne Dosa",
                "lat": 12.9983,
                "lon": 77.5924,
                "rating": 4.8,
                "category": "🥤 Famous Food",
                "address": "220 m"
            },
            {
                "name": "Palace View Point",
                "lat": 12.9979,
                "lon": 77.5929,
                "rating": 4.9,
                "category": "📸 Tourist Spot",
                "address": "80 m"
            },
            {
                "name": "ICICI ATM",
                "lat": 12.9974,
                "lon": 77.5925,
                "rating": 4.2,
                "category": "💳 ATM",
                "address": "40 m"
            },
            {
                "name": "Taxi Stand",
                "lat": 12.9972,
                "lon": 77.5928,
                "rating": 4.1,
                "category": "🚕 Taxi",
                "address": "55 m"
            },
            {
                "name": "Manipal Hospital",
                "lat": 12.9987,
                "lon": 77.5940,
                "rating": 4.6,
                "category": "🏥 Hospital",
                "address": "300 m"
            }
        ]

    return []