import asyncio
from typing import List, Dict, Any
from .scrapers.bus_scraper import BusScraper
from .scrapers.train_scraper import TrainScraper
from .scrapers.flight_scraper import FlightScraper

class TransportManager:
    """Orchestrates scraping concurrent requests, handles retries/fallbacks, and aggregates results."""

    def __init__(self):
        self.bus_scraper = BusScraper()
        self.train_scraper = TrainScraper()
        self.flight_scraper = FlightScraper()

    async def search_all(self, from_city: str, to_city: str, date: str, modes: List[str]) -> Dict[str, Dict[str, Any]]:
        """Executes concurrent scraper requests for each requested mode."""
        tasks = []
        mode_keys = []

        # Map each mode to its scraping task
        for mode in modes:
            m_clean = mode.strip().title()
            if m_clean == "Bus":
                tasks.append(self.bus_scraper.search(from_city, to_city, date))
                mode_keys.append("Bus")
            elif m_clean == "Train":
                tasks.append(self.train_scraper.search(from_city, to_city, date))
                mode_keys.append("Train")
            elif m_clean == "Flight":
                tasks.append(self.flight_scraper.search(from_city, to_city, date))
                mode_keys.append("Flight")

        if not tasks:
            return {}

        print(f"[TransportManager] Initiating concurrent search for modes: {mode_keys}")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        aggregated = {}
        for mode, result in zip(mode_keys, results):
            if isinstance(result, Exception):
                print(f"[TransportManager] Scraper exception for {mode}: {result}")
                aggregated[mode] = {
                    "status": "failed",
                    "reason": f"Exception: {str(result)}",
                    "tickets": []
                }
            else:
                aggregated[mode] = result

        return aggregated
