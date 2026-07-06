# crowd_api.py
from fastapi import APIRouter
from database.postgres import get_connection
from services.crowdcache import getcrowd

router = APIRouter()

@router.get("/api/crowd")
def crowdendpoint(city: str, attraction: str):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                a.popularity_level,
                a.best_visit_time
            FROM attraction_details a
            JOIN destinations d
                ON d.id = a.destination_id
            WHERE LOWER(d.destination_name)=LOWER(%s)
              AND LOWER(a.attraction_name)=LOWER(%s)
            LIMIT 1
        """, (city, attraction))

        row = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    if not row:
        return {"error": "attraction not found"}

    popularity = row[0] or "Medium"
    besttime = row[1] or "Morning"

    return getcrowd(
        city,
        attraction,
        popularity,
        besttime
    )