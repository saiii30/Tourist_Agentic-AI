import sys
import types
import unittest

from backend.AI.agents.calendar_builder import CalendarBuilder


class CalendarBuilderSequenceTests(unittest.TestCase):
    def setUp(self):
        osrm = types.ModuleType("services.osrm_service")
        osrm.geocode_place = lambda place, city: (10.0, 77.0)
        osrm.get_osrm_route = lambda lat1, lng1, lat2, lng2: (
            round(abs(lat2 - lat1) * 100 + abs(lng2 - lng1) * 100, 1),
            round((abs(lat2 - lat1) * 100 + abs(lng2 - lng1) * 100) * 4, 1),
        )
        sys.modules["services.osrm_service"] = osrm

    def test_daily_anchors_and_return_boarding_are_preserved(self):
        hotels = [{"id": "h1", "hotel_id": "h1", "name": "Lake Hotel", "latitude": 10.0, "longitude": 77.0, "rating": 4.5}]
        restaurants = [
            {"id": "r1", "restaurant_id": "r1", "name": "Breakfast Cafe", "latitude": 10.001, "longitude": 77.001, "serves_breakfast": True},
            {"id": "r2", "restaurant_id": "r2", "name": "Town Restaurant", "latitude": 10.002, "longitude": 77.002},
            {"id": "r3", "restaurant_id": "r3", "name": "Garden Restaurant", "latitude": 10.003, "longitude": 77.003},
        ]
        attractions = [
            {"id": f"a{i}", "attraction_id": f"a{i}", "name": name, "latitude": 10.004 + i / 1000, "longitude": 77.004 + i / 1000, "rating": 4.5, "types": types_}
            for i, (name, types_) in enumerate([
                ("Lake View", ["park"]),
                ("Museum", ["museum"]),
                ("Local Market", ["market", "store"]),
                ("Hill View", ["natural_feature"]),
                ("Garden", ["park"]),
                ("Craft Bazaar", ["market"]),
            ])
        ]
        tickets = [
            {"id": "out", "direction": "outbound", "mode": "Train", "carrier": "Outbound Express", "departure": "06:00", "arrival": "11:00", "duration": "5h", "price": 500},
            {"id": "ret", "direction": "return", "mode": "Train", "carrier": "Return Express", "departure": "18:00", "arrival": "23:00", "duration": "5h", "price": 500},
        ]

        result = CalendarBuilder.build_itinerary(
            city="Kodaikanal", start_date_str="2026-08-12", days=3,
            budget="Moderate", travel_style="Family", interests="Nature, Shopping",
            travelers=4, hotels=hotels, restaurants=restaurants,
            attractions=attractions, weather={"main": "Clear"},
            current_location="Chennai", travel_mode="Train", transport_data=tickets,
            preferred_start_time="10:00", preferred_end_time="18:00",
        )

        middle_types = [item["type"] for item in result["days"][1]["activities"]]
        self.assertEqual(middle_types[0], "Breakfast")
        self.assertIn("Lunch", middle_types)
        self.assertIn("Dinner", middle_types)
        self.assertEqual(middle_types[-1], "Hotel")
        self.assertTrue(all("distance" in item and "travel_time" in item for item in result["days"][1]["activities"]))

        final = result["days"][-1]["activities"]
        self.assertEqual(final[-1]["category"], "Transport")
        self.assertIn("Return Express", final[-1]["title"])
        self.assertEqual(final[-1]["start_time"], "18:00")


if __name__ == "__main__":
    unittest.main()
