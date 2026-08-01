from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_fixed
import asyncio
import json
import re
import sys
import os

class TrainScraper:
    """Class to handle ConfirmTkt train scraping operations using direct URL"""

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
    async def search_trains(self, url: str, output_path: str = "train_results.json") -> list:
        """Execute the train search with retry capability using a direct URL"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
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
                
                # Wait for schedule buttons to appear
                print("Waiting for train search results to render...")
                await page.wait_for_selector("button:has-text('Schedule')", timeout=20000)
                
                # Scroll down in small increments to lazy-load elements
                for _ in range(5):
                    await page.mouse.wheel(0, 1000)
                    await page.wait_for_timeout(400)
                
                # Scroll back to top
                await page.mouse.wheel(0, -5000)
                await page.wait_for_timeout(500)

                # Extract the page text inside the body
                content = await page.locator("body").inner_text()
                
                # Find all trains using regular expressions
                pattern = re.compile(
                    r'(\d{5})([^\n]+)\n+([\d.]+)\n+(\d{2}:\d{2})\s+(\w+)\n+(\d+h\s+\d+m|\d+h|\d+m)\n+(\d{2}:\d{2})\s+(\w+)\n+Schedule'
                )
                
                matches = pattern.findall(content)
                results = []
                
                print(f"Found {len(matches)} trains matched by regex.")

                for match in matches:
                    number, name, rating, dep_time, dep_station, duration, arr_time, arr_station = match
                    
                    number = number.strip()
                    name = name.strip()
                    dep_time = dep_time.strip()
                    arr_time = arr_time.strip()
                    duration = duration.strip()
                    
                    # Convert duration string (e.g. 6h 45m) to minutes
                    h_match = re.search(r'(\d+)\s*h', duration)
                    m_match = re.search(r'(\d+)\s*m', duration)
                    h = int(h_match.group(1)) if h_match else 0
                    m = int(m_match.group(1)) if m_match else 0
                    duration_mins = h * 60 + m
                    
                    # Determine train type from name
                    name_lower = name.lower()
                    if "vandebharat" in name_lower or "vande bharat" in name_lower:
                        train_type = "Vande Bharat"
                    elif "shatabdi" in name_lower:
                        train_type = "Shatabdi"
                    elif "rajdhani" in name_lower:
                        train_type = "Rajdhani"
                    elif "duronto" in name_lower:
                        train_type = "Duronto"
                    elif "humsafar" in name_lower:
                        train_type = "Humsafar"
                    elif "sf" in name_lower or "superfast" in name_lower:
                        train_type = "Superfast"
                    else:
                        train_type = "Express"

                    results.append({
                        "train": {
                            "number": number,
                            "name": name,
                            "type": train_type,
                            "runDays": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
                        },
                        "from": {
                            "departure": dep_time,
                            "arrival": None,
                            "day": 1,
                            "sequence": 1
                        },
                        "to": {
                            "departure": None,
                            "arrival": arr_time,
                            "day": 1,
                            "sequence": 10
                        },
                        "distance": 0,
                        "duration": duration_mins,
                        "totalHaltsBetween": 0
                    })
                
                output_data = {
                    "search_url": url,
                    "trains": results
                }
                
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(output_data, f, indent=4, ensure_ascii=False)
                
                print(f"Train data saved successfully to {output_path}")
                return results

            finally:
                await browser.close()

async def main():
    if len(sys.argv) > 2:
        url = sys.argv[1]
        output_path = sys.argv[2]
    elif len(sys.argv) > 1:
        url = sys.argv[1]
        output_path = "train_results.json"
    else:
        url = "https://www.confirmtkt.com/rbooking/trains/from/MAS/to/SBC/30-07-2026"
        output_path = "train_results.json"

    scraper = TrainScraper()
    try:
        trains = await scraper.search_trains(url, output_path)
        print(f"Successfully found {len(trains)} trains")
    except Exception as e:
        print(f"Error during train search: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
