# crowd_api.py
from fastapi import APIRouter
from database.postgres import get_connection
from services.crowdcache import getcrowd

router = APIRouter()

@router.get("/api/crowd")
def crowdendpoint(
    city: str,
    attraction: str = "",
    popularity: str = "Medium",
    besttime: str = "Morning",
    scope: str = "attraction",
):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if scope == "city":
            # This is an aggregate for the destination, not a prediction for a
            # fictitious attraction named e.g. "Jaipur overall".
            cursor.execute("""
                SELECT a.popularity_level
                FROM attraction_details a
                JOIN destinations d ON d.id = a.destination_id
                WHERE LOWER(d.destination_name) = LOWER(%s)
            """, (city,))
            popularity_rows = cursor.fetchall()
            popularity_points = {"popular": 5, "medium": 3}
            average = (
                sum(popularity_points.get((row[0] or "").lower(), 1) for row in popularity_rows)
                / len(popularity_rows)
                if popularity_rows
                else 3
            )
            popularity = "Popular" if average >= 4 else "Medium" if average >= 2 else "Low"
            # A city has no single "best visit" hour, so do not apply that bonus.
            besttime = "All day"
            attraction = f"{city} overall"
        else:
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

    # if not row:
    #     return {"error": "attraction not found"}

    # popularity = row[0] or "Medium"
    # besttime = row[1] or "Morning"
    # Dynamic/AI attraction names may not exist exactly in attraction_details.
# Use the Discover Agent values so the meter still works.
    if scope != "city" and row:
        popularity = row[0] or popularity
        besttime = row[1] or besttime

    return getcrowd(
        city,
        attraction,
        popularity,
        besttime
    )
