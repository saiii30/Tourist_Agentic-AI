from datetime import date, timedelta
import random

from database.postgres import get_connection


def seasonal_multiplier(month):
    """
    Tourism season factor
    """

    # Peak season
    if month in [10, 11, 12]:
        return 1.4

    # Summer travel
    if month in [4, 5, 6]:
        return 1.2

    # Monsoon
    if month in [7, 8]:
        return 0.8

    return 1.0


def weekend_multiplier(weekday):
    """
    Python weekday:
    Monday=0
    Sunday=6
    """

    if weekday in [5, 6]:
        return 1.3

    return 1.0


def hour_band_multiplier(hour_band):

    if hour_band == "morning":
        return 1.2

    if hour_band == "noon":
        return 1.0

    if hour_band == "evening":
        return 1.4

    return 0.6


def popularity_to_base(popularity_score):

    score = float(popularity_score or 50)

    return int(500 + score * 20)


def seed():

    conn = get_connection()
    cursor = conn.cursor()

    print("Loading destinations...")

    cursor.execute(
        """
        SELECT
            destination_name,
            popularity_score
        FROM destinations
        """
    )

    destinations = cursor.fetchall()

    print(f"Found {len(destinations)} destinations")

    cursor.execute("TRUNCATE crowd_history RESTART IDENTITY")
    conn.commit()

    start_date = date.today() - timedelta(days=365 * 3)
    end_date = date.today()

    total_rows = 0

    for city, popularity_score in destinations:

        city = city.strip()

        base_visitors = popularity_to_base(popularity_score)

        current_date = start_date

        while current_date <= end_date:

            season_factor = seasonal_multiplier(
                current_date.month
            )

            weekend_factor = weekend_multiplier(
                current_date.weekday()
            )

            for hour_band in [
                "morning",
                "noon",
                "evening",
                "night",
            ]:

                hour_factor = hour_band_multiplier(
                    hour_band
                )

                visitors = int(
                    base_visitors
                    * season_factor
                    * weekend_factor
                    * hour_factor
                    * random.uniform(0.85, 1.15)
                )

                cursor.execute(
                    """
                    INSERT INTO city_crowd_history
                    (
                        city,
                        visit_date,
                        month,
                        weekday,
                        hour_band,
                        visitors
                    )
                    VALUES
                    (%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        city,
                        current_date,
                        current_date.month,
                        current_date.weekday(),
                        hour_band,
                        visitors,
                    ),
                )

                total_rows += 1

            current_date += timedelta(days=1)

        print(f"Seeded {city}")

    conn.commit()

    print()
    print("DONE")
    print(f"Inserted {total_rows:,} rows")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    seed()