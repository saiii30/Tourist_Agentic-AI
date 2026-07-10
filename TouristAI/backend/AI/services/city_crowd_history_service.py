from datetime import datetime, timedelta

from database.postgres import get_connection


# def _current_hour_band(hour: int) -> str:
#     if 6 <= hour < 12:
#         return "morning"
#     if 12 <= hour < 17:
#         return "afternoon"
#     if 17 <= hour < 22:
#         return "evening"
#     return "night"
def _current_hour_band(hour: int) -> str:
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 16:
        return "noon"
    if 16 <= hour < 21:
        return "evening"
    return "night"

def _crowd_level(score: int) -> tuple[str, str, str]:
    if score >= 14:
        return "Very High", "🔴", "Avoid peak hours if possible."
    if score >= 10:
        return "High", "🟠", "Expect queues; book tickets in advance."
    if score >= 6:
        return "Medium", "🟡", "Moderate crowd expected."
    return "Low", "🟢", "Best time for a peaceful visit."


def predict_city_crowd_from_history(city: str) -> dict:
    """
    City-wide crowd prediction based on the previous three years of records:
    same month + same weekday + same hour band.
    """
    now = datetime.now()
    start_date = (now - timedelta(days=365 * 3)).date()

    # PostgreSQL: Sunday=0, Monday=1 ... Saturday=6
    postgres_weekday = (now.weekday() + 1) % 7
    hour_band = _current_hour_band(now.hour)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Most relevant historical rows: same city/month/weekday/time period.
        cursor.execute(
            """
            SELECT
                COALESCE(AVG(visitors), 0) AS expected_visitors,
                COUNT(*) AS sample_count
            FROM city_crowd_history
            WHERE LOWER(city) = LOWER(%s)
           AND month = %s
  AND weekday = %s
  AND hour_band = %s
            """,
            # (city, start_date, now.month, postgres_weekday, hour_band),
             (city,  now.month, now.weekday(), hour_band),
        )
        expected_visitors, sample_count = cursor.fetchone()

        # Fallback: all city records from the previous three years.
        if not sample_count:
            cursor.execute(
                """
                SELECT
                    COALESCE(AVG(visitors), 0) AS expected_visitors,
                    COUNT(*) AS sample_count
                FROM city_crowd_history
                WHERE LOWER(city) = LOWER(%s)
                  AND visit_date >= %s
                """,
                (city, start_date),
            )
            expected_visitors, sample_count = cursor.fetchone()

        if not sample_count:
            raise ValueError(
                f"No three-year crowd history found for {city}. "
                "Add city_crowd_history records for this city first."
            )

        # The normal historical average for this city.
        cursor.execute(
            """
            SELECT COALESCE(AVG(visitors), 0)
            FROM city_crowd_history
            WHERE LOWER(city) = LOWER(%s)
              AND visit_date >= %s
            """,
            (city, start_date),
        )
        city_baseline = cursor.fetchone()[0] or 1

    finally:
        cursor.close()
        conn.close()

    expected_visitors = float(expected_visitors)
    city_baseline = float(city_baseline)

    # Score compares today's historical pattern with the city's normal level.
    ratio = expected_visitors / city_baseline
    score = max(1, min(20, round(ratio * 10)))

    level, emoji, advice = _crowd_level(score)

    return {
        "city": city,
        "level": level,
        "emoji": emoji,
        "score": score,
        "maxscore": 20,
        "expectedVisitors": round(expected_visitors),
        "sampleCount": sample_count,
        "hourBand": hour_band,
        "reasons": [
            "Based on the previous 3 years of city tourism history",
            f"Same month, weekday and {hour_band} period",
            f"{sample_count} historical records analysed",
        ],
        "advice": advice,
        "updatedat": int(now.timestamp()),
    }