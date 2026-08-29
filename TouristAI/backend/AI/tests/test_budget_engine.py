import os
import sys
import unittest


AI_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if AI_ROOT not in sys.path:
    sys.path.insert(0, AI_ROOT)

from budget.budget_engine import calculate_hybrid_budget


class HybridBudgetEngineTests(unittest.TestCase):
    def setUp(self):
        self.baseline = {
            "breakdown": {
                "accommodation": 3000,
                "food": 1000,
                "transport": 500,
                "tickets": 200,
                "shopping": 300,
            }
        }

    def test_uses_ranked_upstream_prices_without_summing_candidates(self):
        result = calculate_hybrid_budget(
            baseline=self.baseline,
            days=2,
            travelers=2,
            maximum_budget=15000,
            hotels=[{"name": "Selected Hotel", "pricePerNight": 2000}, {"name": "Other", "pricePerNight": 9000}],
            transport=[{"mode": "Train", "price": 1000, "booking_source": "ConfirmTkt"}],
            restaurants=[{"price_range": "₹200 - ₹400"}],
            attractions=[{"name": "Museum", "ticket_price": 100}],
        )

        self.assertEqual(result["breakdown"]["accommodation"], 4000)
        self.assertEqual(result["breakdown"]["intercity_transport"], 2000)
        self.assertEqual(result["breakdown"]["food"], 3600)
        self.assertEqual(result["subtotal"], 11100)
        self.assertEqual(result["estimated_total"], 12210)
        self.assertEqual(result["remaining"], 2790)
        self.assertEqual(result["status"], "within_budget")

    def test_marks_over_budget_and_keeps_fallback_metadata(self):
        result = calculate_hybrid_budget(
            baseline=self.baseline,
            days=2,
            travelers=1,
            maximum_budget=3000,
        )

        self.assertEqual(result["status"], "over_budget")
        self.assertLess(result["remaining"], 0)
        self.assertTrue(result["recommendations"])
        self.assertTrue(any(source["source_type"] == "fallback" for source in result["price_sources"]))

    def test_per_person_budget_scales_by_travelers(self):
        result = calculate_hybrid_budget(
            baseline=self.baseline,
            days=1,
            travelers=3,
            per_person_budget="₹10,000",
        )
        self.assertEqual(result["budget_limit"], 30000)


if __name__ == "__main__":
    unittest.main()
