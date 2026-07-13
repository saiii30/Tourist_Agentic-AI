from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_fixed
from dataclasses import dataclass
from typing import List
import asyncio
import json
import re


@dataclass
class FlightData:
    """Data class to store individual flight information"""

    airline: str
    departure_time: str
    arrival_time: str
    duration: str
    stops: str
    price: str
    co2_emissions: str
    emissions_variation: str


class FlightScraper:
    """Class to handle Google Flights scraping operations using direct URL"""

    SELECTORS = {
        "airline": "div.sSHqwe.tPgKwe.ogfYpf",
        "departure_time": 'span[aria-label^="Departure time"]',
        "arrival_time": 'span[aria-label^="Arrival time"]',
        "duration": 'div[aria-label^="Total duration"]',
        "stops": "div.hF6lYb span.rGRiKd",
        "price": "div.FpEdX span",
        "co2_emissions": "div.O7CXue",
        "emissions_variation": "div.N6PNV",
    }

    async def _extract_text(self, element) -> str:
        """Extract text content from a page element safely"""
        return (await element.text_content()).strip() if element else "N/A"

    async def _load_all_flights(self, page) -> None:
        """Click 'Show more flights' button until all flights are loaded"""
        while True:
            try:
                more_button = await page.wait_for_selector(
                    'button[aria-label*="more flights"]', timeout=5000
                )
                if more_button:
                    await more_button.click()
                    await page.wait_for_timeout(2000)
                else:
                    break
            except:
                break
    async def _extract_flight_data(self, page):
        await page.wait_for_timeout(5000)

        flights = await page.locator("li").evaluate_all("""
        (elements) => {
            const results = [];
            elements.forEach(el => {
                const text = el.innerText;
                if (text.includes("₹") || text.includes("$")) {
                    const lines = text.split("\\n").map(x => x.trim()).filter(x => x !== "");
                    
                    const depTime = lines[0] || "";
                    const arrTimeIdx = lines.findIndex((x, idx) => idx > 0 && (x.includes("AM") || x.includes("PM")));
                    const arrTime = arrTimeIdx !== -1 ? lines[arrTimeIdx] : "";
                    const airline = arrTimeIdx !== -1 && lines[arrTimeIdx + 1] ? lines[arrTimeIdx + 1] : "";
                    
                    const duration = lines.find(x => /^\\d+\\s*h/i.test(x) || /^\\d+\\s*m/i.test(x) || /\\bhr\\b|\\bmin\\b/.test(x)) || "";
                    const stops = lines.find(x => x.toLowerCase().includes("stop") || x.toLowerCase().includes("nonstop")) || "";
                    const price = lines.find(x => x.includes("₹") || x.includes("$")) || "";
                    const co2 = lines.find(x => x.toLowerCase().includes("co2") || x.toLowerCase().includes("co₂")) || "";
                    const variation = lines.find(x => x.includes("%")) || "";
                    
                    results.push({
                        airline: airline,
                        departure_time: depTime,
                        arrival_time: arrTime,
                        duration: duration,
                        stops: stops,
                        price: price,
                        co2_emissions: co2,
                        emissions_variation: variation
                    });
                }
            });
            return results;
        }
        """)

        return flights

    def _extract_trip_info_from_url(self, url: str) -> dict:
        """Extract trip information from Google Flights URL"""
        trip_info = {}
        airport_match = re.search(r"[?&]tfs=.*?([A-Z]{3}).*?([A-Z]{3})", url)
        if airport_match:
            trip_info["origin"] = airport_match.group(1)
            trip_info["destination"] = airport_match.group(2)

        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", url)
        if date_match:
            trip_info["date"] = date_match.group(1)

        return trip_info

    def save_results(self, flights: List[FlightData], url: str) -> str:
        """Save flight search results to a JSON file"""
        output_data = {
            "search_url": url,
            "flights": [vars(flight) for flight in flights],
        }

        filepath = "flight_results.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        return filepath

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
    async def search_flights(self, url: str, output_path: str = "flight_results.json") -> List[FlightData]:
        """Execute the flight search with retry capability using a direct URL"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
                locale="en-US"
            )
            page = await context.new_page()

            try:
                await page.goto(url, timeout=60000)
                await page.wait_for_load_state("networkidle")

                flights = await self._extract_flight_data(page)

                output = {
                    "search_url": url,
                    "flights": flights
                }

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(output, f, indent=4, ensure_ascii=False)

                print(f"Flight data saved successfully to {output_path}")

                return flights
            finally:
                await browser.close()


async def main():
    """Main function to demonstrate usage"""
    import sys
    
    if len(sys.argv) > 2:
        url = sys.argv[1]
        output_path = sys.argv[2]
    elif len(sys.argv) > 1:
        url = sys.argv[1]
        output_path = "flight_results.json"
    else:
        url = "https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI1LTA0LTAxagcIARIDREVMcgcIARIDU0ZPQAFIAXABggELCP___________wGYAQI&curr=USD"
        output_path = "flight_results.json"

    scraper = FlightScraper()
    try:
        flights = await scraper.search_flights(url, output_path)
        print(f"Successfully found {len(flights)} flights")
    except Exception as e:
        print(f"Error during flight search: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())