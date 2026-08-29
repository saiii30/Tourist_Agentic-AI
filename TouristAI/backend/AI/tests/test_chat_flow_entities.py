import os
import sys
import unittest


AI_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if AI_ROOT not in sys.path:
    sys.path.insert(0, AI_ROOT)

from chat_flow import analyze_chat_flow


class ChatFlowEntityTests(unittest.TestCase):
    def test_itinerary_duration_travelers_and_numeric_budget_are_distinct(self):
        plan = analyze_chat_flow("Estimate a 3-day Delhi trip for 2 people under ₹30,000")
        self.assertEqual(plan.intent, "itinerary")
        self.assertEqual(plan.destination, "Delhi")
        self.assertEqual(plan.entities.get("days"), "3")
        self.assertEqual(plan.entities.get("travelers"), "2")
        self.assertEqual(plan.entities.get("budget_amount"), "30000")

    def test_jaipur_information_request_routes_directly_to_rag(self):
        plan = analyze_chat_flow("tell me about jaipur")
        self.assertEqual(plan.intent, "knowledge")
        self.assertEqual(plan.destination, "Jaipur")
        self.assertTrue(plan.should_use_direct_rag)

    def test_unindexed_city_information_request_can_reach_web_fallback(self):
        plan = analyze_chat_flow("tell me about udaipur")
        self.assertEqual(plan.intent, "knowledge")
        self.assertEqual(plan.destination, "Udaipur")
        self.assertTrue(plan.should_use_direct_rag)

    def test_short_interest_reply_stays_in_active_questionnaire(self):
        plan = analyze_chat_flow("History", active_flow=True)
        self.assertFalse(plan.should_use_direct_rag)
        self.assertFalse(plan.should_reset_questionnaire)

    def test_trichy_trip_from_theni_extracts_route_context(self):
        plan = analyze_chat_flow("Plan a 3 day Trichy trip from Theni")
        self.assertEqual(plan.destination, "Trichy")
        self.assertEqual(plan.entities.get("current_location"), "Theni")
        self.assertEqual(plan.entities.get("days"), "3")

    def test_explicit_history_question_can_leave_active_questionnaire_for_rag(self):
        plan = analyze_chat_flow("Tell me about Trichy history", active_flow=True)
        self.assertTrue(plan.should_use_direct_rag)
        self.assertTrue(plan.should_reset_questionnaire)

    def test_specific_weather_request_wins_over_generic_trip_word(self):
        plan = analyze_chat_flow("Will it rain during my Goa trip tomorrow?")
        self.assertEqual(plan.intent, "weather")
        self.assertEqual(plan.destination, "Goa")

    def test_conversational_unknown_weather_city_is_extracted(self):
        plan = analyze_chat_flow("what's the weather like in Paris tomorrow")
        self.assertEqual(plan.intent, "weather")
        self.assertEqual(plan.destination, "Paris")
        self.assertEqual(plan.entities.get("travel_date"), "tomorrow")

    def test_misspelled_itinerary_still_starts_planning(self):
        plan = analyze_chat_flow("make an iternary for Kyoto for 4 days")
        self.assertEqual(plan.intent, "itinerary")
        self.assertEqual(plan.destination, "Kyoto")
        self.assertEqual(plan.entities.get("days"), "4")

    def test_practical_travel_advice_uses_knowledge_pipeline(self):
        plan = analyze_chat_flow("Do Indian citizens need a visa for Japan?")
        self.assertEqual(plan.intent, "knowledge")
        self.assertTrue(plan.should_use_direct_rag)

    def test_numeric_slash_date_is_extracted(self):
        plan = analyze_chat_flow("Find trains from Chennai to Bengaluru on 28/08/2026")
        self.assertEqual(plan.intent, "transport")
        self.assertEqual(plan.entities.get("travel_date"), "28/08/2026")

    def test_train_route_preserves_origin_destination_and_mode(self):
        plan = analyze_chat_flow("Book a train from Chennai to Bengaluru tomorrow")
        self.assertEqual(plan.intent, "transport")
        self.assertEqual(plan.entities.get("current_location"), "Chennai")
        self.assertEqual(plan.entities.get("destination"), "Bengaluru")
        self.assertEqual(plan.entities.get("travel_mode"), "Train")

    def test_destination_only_train_request_does_not_invent_origin(self):
        plan = analyze_chat_flow("Book train for Chennai")
        self.assertEqual(plan.intent, "transport")
        self.assertEqual(plan.entities.get("destination"), "Chennai")
        self.assertNotIn("current_location", plan.entities)


if __name__ == "__main__":
    unittest.main()
