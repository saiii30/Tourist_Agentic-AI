from fastapi import APIRouter
from database.postgres import get_connection
import math

router = APIRouter(prefix="/api")


def haversine(lat1, lon1, lat2, lon2):
    R = 6371

    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)

    a = (
        math.sin(dLat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dLon / 2) ** 2
    )

    return R * 2 * math.asin(math.sqrt(a))


@router.get("/nearby")
def nearby(lat: float, lon: float):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            attraction_name,
            description,
            latitude,
            longitude,
            category
        FROM attraction_details
        WHERE latitude IS NOT NULL
        AND longitude IS NOT NULL
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    result = []

    for row in rows:

        dist = haversine(
            lat,
            lon,
            float(row[2]),
            float(row[3])
        )

        result.append({
            "name": row[0],
            "history": row[1],
            "lat": float(row[2]),
            "lon": float(row[3]),
            "category": row[4],
            "distance": round(dist,2)
        })

    result.sort(key=lambda x: x["distance"])

    return result[:30]