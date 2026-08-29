import unittest

from backend.AI.agents.concierge_agent import concierge_agent


class ConciergeAgentTests(unittest.TestCase):
    def setUp(self):
        self.trip = {
            "cityName": "Delhi",
            "startDate": "2026-08-06",
            "itinerary": {1: [
                {"title": "India Gate", "time": "10:00 AM", "location": "Kartavya Path", "category": "Sightseeing"},
                {"title": "Janpath Market Shopping", "time": "03:00 PM", "category": "Relaxation"},
                {"title": "Delhi Kitchen", "time": "07:00 PM", "category": "Food", "restaurant": "Delhi Kitchen"},
                {"title": "Delhi Hotel", "time": "09:00 PM", "category": "Hotel", "hotel": "Delhi Hotel"},
            ]},
            "budgetSummary": {"estimated_total": 22000, "budget_limit": 30000, "remaining": 8000, "status": "within_budget"},
            "restaurants": [{"name": "Delhi Kitchen", "serves_vegetarian": True}],
            "emergencyContacts": [{"role": "National Helpline", "number": "112"}],
        }

    def test_budget_is_read_only(self):
        result = concierge_agent("How much budget is remaining?", self.trip)
        self.assertEqual(result["intent"], "budget")
        self.assertFalse(result["requires_confirmation"])
        self.assertIn("8,000", result["answer"])

    def test_modification_requires_confirmation(self):
        result = concierge_agent("Replace my hotel", self.trip)
        self.assertTrue(result["requires_confirmation"])
        self.assertEqual(result["proposed_action"]["type"], "replace_hotel")

    def test_activity_replacement_is_structured(self):
        result = concierge_agent("Replace India Gate with Red Fort", self.trip)
        self.assertTrue(result["requires_confirmation"])
        self.assertEqual(result["proposed_action"]["type"], "replace_activity")
        self.assertEqual(result["proposed_action"]["target"], "India Gate")
        self.assertEqual(result["proposed_action"]["replacement"], "Red Fort")

    def test_incomplete_activity_replacement_explains_required_format(self):
        result = concierge_agent("Replace an activity", self.trip)
        self.assertFalse(result["requires_confirmation"])
        self.assertIn("both activity names", result["answer"])

    def test_itinerary_summary_groups_trip_content(self):
        result = concierge_agent("Check my itinerary", self.trip)
        self.assertEqual(result["intent"], "itinerary_summary")
        self.assertIn("Attractions: India Gate", result["answer"])
        self.assertIn("Shopping: Janpath Market Shopping", result["answer"])
        self.assertIn("Hotel: Delhi Hotel", result["answer"])
        self.assertIn("Restaurants: Delhi Kitchen", result["answer"])

    def test_remove_activity_is_structured(self):
        result = concierge_agent("Remove India Gate from my itinerary", self.trip)
        self.assertTrue(result["requires_confirmation"])
        self.assertEqual(result["proposed_action"]["type"], "remove_activity")
        self.assertEqual(result["proposed_action"]["target"], "India Gate")

    def test_add_activity_has_day_and_time(self):
        result = concierge_agent("Add Red Fort on day 2 at 3:00 PM", self.trip)
        self.assertTrue(result["requires_confirmation"])
        self.assertEqual(result["proposed_action"]["type"], "add_activity")
        self.assertEqual(result["proposed_action"]["activity"], "Red Fort")
        self.assertEqual(result["proposed_action"]["day"], 2)
        self.assertEqual(result["proposed_action"]["time"], "3:00 PM")

    def test_emergency_prioritizes_112(self):
        result = concierge_agent("I need emergency help", self.trip)
        self.assertEqual(result["priority"], "critical")
        self.assertIn("112", result["answer"])

    def test_weather_refinement_is_a_confirmable_action(self):
        result = concierge_agent("Adjust day 1 for rain", self.trip)
        self.assertTrue(result["requires_confirmation"])
        self.assertEqual(result["proposed_action"]["type"], "adapt_to_weather")
        self.assertEqual(result["proposed_action"]["day"], 1)

    def test_crowd_refinement_is_supported(self):
        result = concierge_agent("Avoid crowds on day 1", self.trip)
        self.assertEqual(result["proposed_action"]["type"], "adapt_to_crowd")

    def test_single_day_regeneration_preserves_scope(self):
        result = concierge_agent("Regenerate day 2", self.trip)
        self.assertEqual(result["proposed_action"]["type"], "regenerate_day")
        self.assertEqual(result["proposed_action"]["day"], 2)

    def test_accessibility_refinement_collects_needs(self):
        result = concierge_agent("Make this wheelchair accessible with reduced walking", self.trip)
        self.assertEqual(result["proposed_action"]["type"], "make_accessible")
        self.assertIn("wheelchair", result["proposed_action"]["accessibility_needs"])

    def test_budget_target_is_calculated_from_current_total(self):
        result = concierge_agent("Reduce my budget by 25%", self.trip)
        action = result["proposed_action"]
        self.assertEqual(action["type"], "adjust_budget")
        self.assertEqual(action["target_total"], 16500)

    def test_transport_replacement_uses_destination_mode(self):
        result = concierge_agent("Switch transport from train to bus", self.trip)
        self.assertEqual(result["proposed_action"]["type"], "replace_transport")
        self.assertEqual(result["proposed_action"]["travel_mode"], "Bus")

    def test_schedule_audit_detects_duplicate_times(self):
        self.trip["itinerary"][1].append({"title": "Red Fort", "time": "10:00 AM", "category": "Sightseeing", "location": "Delhi"})
        result = concierge_agent("Check conflicts in my itinerary", self.trip)
        self.assertEqual(result["intent"], "trip_audit")
        self.assertTrue(any(issue["type"] == "time_conflict" for issue in result["data"]["issues"]))


if __name__ == "__main__":
    unittest.main()
