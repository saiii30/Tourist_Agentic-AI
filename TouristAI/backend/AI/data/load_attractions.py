import os
import sys
import json

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from database.postgres import get_connection

# Load JSON
with open("india_tourism_dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

conn = get_connection()
cursor = conn.cursor()

for item in data:

    destination_name = item.get("destination_name")

    # Find destination id
    cursor.execute(
        """
        SELECT id
        FROM destinations
        WHERE destination_name=%s
        """,
        (destination_name,)
    )

    result = cursor.fetchone()

    if not result:
        print(f"Destination not found : {destination_name}")
        continue

    destination_id = result[0]

    # -----------------------------
    # Primary Attractions
    # -----------------------------

    for attraction in item.get("primary_attractions", []):

        cursor.execute(
            """
            INSERT INTO attraction_details(

                destination_id,
                attraction_name,
                category,
                description,
                popularity_level,
                risk_level,
                family_friendly,
                best_visit_time,
                visit_duration

            )

            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (

                destination_id,
                attraction,
                "Tourist Attraction",
                "",
                "Popular",
                "Low",
                True,
                "Morning",
                "2 Hours"

            )
        )

    # -----------------------------
    # Hidden Gems
    # -----------------------------

    for attraction in item.get("hidden_gems", []):

        cursor.execute(
            """
            INSERT INTO attraction_details(

                destination_id,
                attraction_name,
                category,
                description,
                popularity_level,
                risk_level,
                family_friendly,
                best_visit_time,
                visit_duration

            )

            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (

                destination_id,
                attraction,
                "Hidden Place",
                "",
                "Hidden",
                "Medium",
                True,
                "Morning",
                "1 Hour"

            )
        )

conn.commit()

cursor.close()
conn.close()

print("Attractions Imported Successfully")