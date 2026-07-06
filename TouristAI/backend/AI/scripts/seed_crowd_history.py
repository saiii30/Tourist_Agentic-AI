"""
Seed 3 years of synthetic-but-realistic crowd history for every attraction
already present in `attraction_details`.

Run once:  python scripts/seed_crowd_history.py
"""

import hashlib
import random
from datetime import date, timedelta

from database.postgres import get_connection


HOUR_BANDS = ("morning", "noon", "evening", "night")

# base daily visitors by popularity level
POP_BASE = {
    "Popular": 4000,
    "Medium":  1500,
    "Hidden":  400,
}

# monthly multiplier — winter peak, monsoon dip (India tourism pattern)
MONTH_MULT = {
    1: 1.30, 2: 1.25, 3: 1.10, 4: 0.95, 5: 0.85, 6: 0.70,
    7: 0.65, 8: 0.70, 9: 0.85, 10: 1.10, 11: 1.25, 12: 1.40,
}

# weekday multiplier — Mon..Sun
WEEKDAY_MULT = [0.75, 0.72, 0.78, 0.82, 0.95, 1.45, 1.55]

# hour band split of the day's total
BAND_SPLIT = {"morning": 0.30, "noon": 0.20, "evening": 0.40, "night": 0.10}


def stable_noise(seed_str: str) -> float:
    """Deterministic 0.85 – 1.15 multiplier so re-runs give same numbers."""
    h = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return 0.85 + (h % 1000) / 1000 * 0.30


def seed():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT d.destination_name, a.attraction_name, a.popularity_level
        FROM attraction_details a
        JOIN destinations d ON d.id = a.destination_id
    """)
    rows = cur.fetchall()
    print(f"Seeding history for {len(rows)} attractions...")

    end = date.today()
    start = end - timedelta(days=365 * 3)

    insert_sql = """
        INSERT INTO crowd_history
            (city, attraction, visit_date, weekday, month, hour_band, visitors)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (city, attraction, visit_date, hour_band) DO NOTHING
    """

    batch = []
    for city, attraction, pop in rows:
        base = POP_BASE.get(pop or "Medium", 1500)
        d = start
        while d <= end:
            month_m = MONTH_MULT[d.month]
            wk_m = WEEKDAY_MULT[d.weekday()]
            noise = stable_noise(f"{city}|{attraction}|{d.isoformat()}")
            day_total = base * month_m * wk_m * noise

            for band, split in BAND_SPLIT.items():
                visitors = int(day_total * split)
                batch.append((
                    city, attraction, d,
                    d.weekday(), d.month, band, visitors,
                ))
            d += timedelta(days=1)

            if len(batch) >= 5000:
                cur.executemany(insert_sql, batch)
                conn.commit()
                batch.clear()

    if batch:
        cur.executemany(insert_sql, batch)
        conn.commit()

    cur.close()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    seed()
