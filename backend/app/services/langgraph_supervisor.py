// backend/app/services/langgraph_supervisor.py
import asyncio
import random
from typing import Dict, Any, List
from app.services.cache import publish


class LangGraphSupervisor:
    """Mock supervisor that simulates planning steps and produces a sample itinerary.
    In a production system this would orchestrate real agents/services.
    """

    def __init__(self, trip_id: str):
        self.trip_id = trip_id
        self.channel = f"trip:{trip_id}"
        # Define the sequence of agents and their status messages
        self.agents = [
            ("request", "Understanding Request..."),
            ("route", "Finding Route..."),
            ("transport", "Searching Transport..."),
            ("tickets", "Comparing Tickets..."),
            ("hotel", "Finding Hotels..."),
            ("restaurant", "Finding Restaurants..."),
            ("weather", "Checking Weather..."),
            ("budget", "Calculating Budget..."),
            ("itinerary", "Building Itinerary..."),
        ]

    async def run(self, trip_data: Dict[str, Any]):
        """Run the mock planning pipeline.
        Args:
            trip_data: The payload received from the frontend (origin, destination, dates, etc.)
        """
        # Simulate progress updates for each agent
        for agent_name, msg in self.agents:
            await self._publish_status(agent_name, msg, 0)
            # Increment progress in a few steps to give a realistic feel
            for progress in range(0, 101, 35):
                await asyncio.sleep(0.3)
                await self._publish_status(agent_name, msg, progress)
            await self._publish_complete(agent_name, {"detail": f"{agent_name} done"})

        # After all agents complete, generate a mock itinerary based on the input data
        itinerary = self._generate_mock_itinerary(trip_data)
        await self._publish_itinerary(itinerary)

    # ---------------------------------------------------------------------
    # Helper methods to publish messages to the Redis channel
    # ---------------------------------------------------------------------
    async def _publish_status(self, agent: str, message: str, progress: int):
        payload = {
            "event": "status",
            "trip_id": self.trip_id,
            "agent": agent,
            "status": "running",
            "progress": progress,
            "message": message,
        }
        publish(self.channel, payload)

    async def _publish_complete(self, agent: str, data: dict):
        payload = {
            "event": "agent_complete",
            "trip_id": self.trip_id,
            "agent": agent,
            "data": data,
        }
        publish(self.channel, payload)

    async def _publish_itinerary(self, data: dict):
        payload = {
            "event": "itinerary_ready",
            "trip_id": self.trip_id,
            "data": data,
        }
        publish(self.channel, payload)

    # ---------------------------------------------------------------------
    # Mock itinerary generator – creates sample data for UI rendering
    # ---------------------------------------------------------------------
    def _generate_mock_itinerary(self, trip_data: Dict[str, Any]) -> Dict[str, Any]:
        destination = trip_data.get("destination") or "Unknown"
        origin = trip_data.get("origin") or "Current Location"
        duration = trip_data.get("duration_days") or 3
        budget = trip_data.get("budget_usd") or 500
        travelers = trip_data.get("travelers") or 1
        interests = trip_data.get("interests") or []

        # Simple helper to create dummy items
        def dummy_places(prefix: str, count: int) -> List[Dict[str, Any]]:
            return [
                {
                    "name": f"{prefix} {i+1}",
                    "location": {
                        "lat": round(12.9 + random.random() * 0.1, 6),
                        "lng": round(77.6 + random.random() * 0.1, 6),
                    },
                    "rating": round(random.uniform(3.5, 4.8), 1),
                }
                for i in range(count)
            ]

        # Generate mock data – ensure we have at least one item for each category
        attractions = dummy_places("Attraction", max(1, len(interests)))
        hotels = dummy_places("Hotel", 3)
        restaurants = dummy_places("Restaurant", 4)
        route = [
            {"lat": 12.9716, "lng": 77.5946},  # Example coordinates (Bangalore)
            {"lat": 13.0827, "lng": 80.2707},
        ]
        distance_km = round(random.uniform(20, 150), 1)
        estimated_budget = int(budget * travelers * 1.2)  # simple multiplier for demo
        forecast = {"temp": random.randint(20, 30)}

        return {
            "origin": origin,
            "destination": destination,
            "duration_days": duration,
            "budget_usd": budget,
            "travelers": travelers,
            "interests": interests,
            "attractions": attractions,
            "hotels": hotels,
            "restaurants": restaurants,
            "route": route,
            "distance_km": distance_km,
            "estimated_budget": estimated_budget,
            "forecast": forecast,
        }

    # End of LangGraphSupervisor
