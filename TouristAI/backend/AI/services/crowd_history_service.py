"""
Historical crowd baseline from 3 years of visitor data.

Public API:
    get_history_score(city, attraction) -> dict | None
        {
            "avg_this_slot":  float,     # avg visitors for month+weekday+hour_band
            "avg_overall":    float,     # avg across all history
            "ratio":          float,     # slot / overall  (1.0 == normal)
            "history_score":  int,       # 0..10 baseline contribution
            "samples":        int,
        }
    Returns None if the attraction has no history rows.
"""

from datetime import datetime
from database.postgres import get_connection


def _hour_band(hour: int) -> str:
    if 5 <= hour < 12:  return "morning"
    if 12 <= hour < 16: return "noon"
    if 16 <= hour < 21: return "evening"
    return "night"


def get_history_score(city: str, attraction: str) -> dict | None:
    if not city or not attraction:
        return None

    now = datetime.now()
    band = _hour_band(now.hour)
    weekday = now.weekday()
    month = now.month

    conn = get_connection()
    cur = conn.cursor()
    try:
        # slot-specific avg
        cur.execute("""
            SELECT AVG(visitors), COUNT(*)
            FROM crowd_history
            WHERE LOWER(city)=LOWER(%s)
              AND LOWER(attraction)=LOWER(%s)
              AND month=%s AND weekday=%s AND hour_band=%s
        """, (city, attraction, month, weekday, band))
        slot_avg, slot_n = cur.fetchone()

        # overall avg for this attraction
        cur.execute("""
            SELECT AVG(visitors), COUNT(*)
            FROM crowd_history
            WHERE LOWER(city)=LOWER(%s)
              AND LOWER(attraction)=LOWER(%s)
        """, (city, attraction))
        all_avg, all_n = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if not all_avg or not slot_avg or all_n == 0:
        return None

    ratio = float(slot_avg) / float(all_avg) if all_avg else 1.0
    # map ratio -> 0..10 contribution
    #   0.5x -> 2 ,  1.0x -> 5 ,  1.5x -> 8 ,  2.0x -> 10
    history_score = max(0, min(10, round(2 + (ratio - 0.5) * 8)))

    return {
        "avg_this_slot": round(float(slot_avg), 1),
        "avg_overall":   round(float(all_avg), 1),
        "ratio":         round(ratio, 2),
        "history_score": int(history_score),
        "samples":       int(slot_n),
    }
