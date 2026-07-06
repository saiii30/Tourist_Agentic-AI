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

with open("india_tourism_dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

conn = get_connection()
cursor = conn.cursor()

for item in data:

    cursor.execute("""
        INSERT INTO destinations(
            destination_name,
            state,
            region,
            popularity_score,
            safety_rating,
            hidden_gems,
            primary_attractions,
            activities_available,
            trip_types,
            ideal_days
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """,
    (
        item.get("destination_name"),
        item.get("state"),
        item.get("region"),
        item.get("popularity_score"),
        item.get("safety_rating"),
        json.dumps(item.get("hidden_gems", [])),
        json.dumps(item.get("primary_attractions", [])),
        json.dumps(item.get("activities_available", [])),
        json.dumps(item.get("trip_types", [])),
        item.get("ideal_days")
    ))

conn.commit()

cursor.close()
conn.close()

print("Data Imported Successfully")