from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_fixed
import asyncio
import json
import re
import sys
import os

class BusScraper:
    """Class to handle redBus scraping operations using direct URL"""

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
    async def search_buses(self, url: str, output_path: str = "bus_results.json") -> list:
        """Execute the bus search with retry capability using a direct URL"""
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
                locale="en-US",
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()

            try:
                print(f"Navigating to {url}...")
                await page.goto(url, timeout=60000)
                await page.wait_for_load_state("domcontentloaded")
                
                # Wait for tuple wrapper (bus cards) to appear
                print("Waiting for bus search results to render...")
                await page.wait_for_selector("li[class*='tupleWrapper']", timeout=20000)
                
                # Scroll down in small increments to lazy-load elements
                for _ in range(3):
                    await page.mouse.wheel(0, 800)
                    await page.wait_for_timeout(500)
                
                # Scroll back to top
                await page.mouse.wheel(0, -3000)
                await page.wait_for_timeout(500)

                # Get all card locators
                cards = await page.locator("li[class*='tupleWrapper']").all()
                results = []
                
                print(f"Found {len(cards)} bus cards on the page.")

                for card in cards:
                    try:
                        label = await card.get_attribute("aria-label")
                        if not label:
                            continue
                        
                        # Parsing using regexes
                        # Example: V Bus Holidays, Bharat Benz A/C Sleeper (2+1). Departs 23:10, arrives 06:00. Duration 6h 50m. Available seats 28 Seats. Price 1278 INR. Rated 4.9 out of 5. Total reviewers 1094.
                        operator_match = re.search(r"^([^,]+)", label)
                        type_match = re.search(r",\s*(.*?)\.\s*Departs", label)
                        dep_match = re.search(r"Departs\s*(\d{2}:\d{2})", label)
                        arr_match = re.search(r"arrives\s*(\d{2}:\d{2})", label)
                        dur_match = re.search(r"Duration\s*(.*?)\.", label)
                        price_match = re.search(r"Price\s*(\d+)", label)
                        rating_match = re.search(r"Rated\s*([\d.]+)\s*out of 5", label)
                        
                        operator = operator_match.group(1).strip() if operator_match else "Unknown Operator"
                        bus_type = type_match.group(1).strip() if type_match else "Standard Bus"
                        departure_time = dep_match.group(1).strip() if dep_match else "N/A"
                        arrival_time = arr_match.group(1).strip() if arr_match else "N/A"
                        duration = dur_match.group(1).strip() if dur_match else "N/A"
                        price_val = price_match.group(1).strip() if price_match else "N/A"
                        rating = rating_match.group(1).strip() if rating_match else "N/A"
                        
                        # Format price to match frontend expectations (e.g. ₹950)
                        price = f"₹{price_val}" if price_val != "N/A" else "N/A"
                        
                        results.append({
                            "operator": operator,
                            "type": bus_type,
                            "departure_time": departure_time,
                            "arrival_time": arrival_time,
                            "duration": duration,
                            "price": price,
                            "rating": rating
                        })
                    except Exception as card_err:
                        print(f"Error parsing individual bus card: {card_err}")
                
                output_data = {
                    "search_url": url,
                    "buses": results
                }
                
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(output_data, f, indent=4, ensure_ascii=False)
                
                print(f"Bus data saved successfully to {output_path}")
                return results

            finally:
                await browser.close()

async def main():
    if len(sys.argv) > 2:
        url = sys.argv[1]
        output_path = sys.argv[2]
    elif len(sys.argv) > 1:
        url = sys.argv[1]
        output_path = "bus_results.json"
    else:
        url = "https://www.redbus.in/bus-tickets/chennai-to-bangalore?doj=30-Jul-2026"
        output_path = "bus_results.json"

    scraper = BusScraper()
    try:
        buses = await scraper.search_buses(url, output_path)
        print(f"Successfully found {len(buses)} buses")
    except Exception as e:
        print(f"Error during bus search: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
