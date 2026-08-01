import os
import sys
import json
import uuid
import tempfile
import asyncio
import subprocess
import re
from datetime import datetime

class FlightScraper:
    """Wrapper to safely execute google_flights_script.py in a separate process to avoid event loop issues."""

    def __init__(self):
        self.script_path = os.path.join(os.path.dirname(__file__), "google_flights_script.py")

    def _get_airport_code(self, name: str) -> str:
        """Translate city name to 3-letter IATA airport code."""
        cleaned_name = re.sub(r'\s+', '', name).upper()
        
        # If it's already a valid 3-letter code, use it directly
        if len(cleaned_name) == 3 and cleaned_name.isalpha():
            return cleaned_name

        city_to_code = {
            'CHENNAI': 'MAA',
            'MADURAI': 'IXM',
            'COIMBATORE': 'CJB',
            'BANGALORE': 'BLR',
            'BENGALURU': 'BLR',
            'DELHI': 'DEL',
            'NEWDELHI': 'DEL',
            'MUMBAI': 'BOM',
            'KOLKATA': 'CCU',
            'HYDERABAD': 'HYD',
            'SALEM': 'SXV',
            'TRICHY': 'TRZ',
            'TIRUCHIRAPPALLI': 'TRZ',
            'TIRUNELVELI': 'TCR', # Tuticorin is near Tirunelveli
            'TUTICORIN': 'TCR',
            'PUDUCHERRY': 'PNY',
            'PONDICHERRY': 'PNY'
        }

        if cleaned_name in city_to_code:
            return city_to_code[cleaned_name]

        # Try partial match
        for city, code in city_to_code.items():
            if cleaned_name in city or city in cleaned_name:
                return code

        return cleaned_name # fallback

    async def search(self, from_city: str, to_city: str, date: str) -> dict:
        """Run the Google Flights script and return status and flights list."""
        if not os.path.exists(self.script_path):
            return {"status": "failed", "reason": f"Scraper script not found at {self.script_path}", "tickets": []}

        from_code = self._get_airport_code(from_city)
        to_code = self._get_airport_code(to_city)
        
        # Format date should be YYYY-MM-DD
        clean_date = date.strip()
        if len(clean_date) != 10 or "-" not in clean_date:
            dt = datetime.now() + datetime.timedelta(days=15)
            clean_date = dt.strftime("%Y-%m-%d")

        search_url = f"https://www.google.com/travel/flights/search?q=Flights%20from%20{from_code}%20to%20{to_code}%20on%20{clean_date}&curr=INR"
        temp_json_path = os.path.join(tempfile.gettempdir(), f"temp_flights_{uuid.uuid4().hex}.json")

        def get_python_executable() -> str:
            scrapers_dir = os.path.dirname(os.path.abspath(__file__))
            tourist_ai_dir = os.path.abspath(os.path.join(scrapers_dir, "..", "..", "..", ".."))
            venv1_py = os.path.join(tourist_ai_dir, ".venv-1", "Scripts", "python.exe")
            if os.path.exists(venv1_py):
                return venv1_py
            venv_py = os.path.join(tourist_ai_dir, ".venv", "Scripts", "python.exe")
            if os.path.exists(venv_py):
                return venv_py
            return sys.executable

        cmd = [get_python_executable(), self.script_path, search_url, temp_json_path]
        print(f"[FlightScraper] Running: {' '.join(cmd)}")

        try:
            proc_res = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                timeout=90
            )

            if proc_res.returncode != 0:
                print(f"[FlightScraper] Failed with exit code {proc_res.returncode}. Stderr: {proc_res.stderr}")
                return {"status": "failed", "reason": f"Subprocess exited with code {proc_res.returncode}", "tickets": []}

            if os.path.exists(temp_json_path):
                try:
                    with open(temp_json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    flights = data.get("flights", [])
                    # Inject booking URL for each flight
                    for flight in flights:
                        flight["booking_url"] = search_url

                    return {"status": "success", "tickets": flights}
                finally:
                    try:
                        os.remove(temp_json_path)
                    except Exception:
                        pass

            return {"status": "failed", "reason": "Output JSON file not created", "tickets": []}

        except subprocess.TimeoutExpired:
            print("[FlightScraper] Scraping timed out after 90 seconds.")
            return {"status": "failed", "reason": "Scraping timed out", "tickets": []}
        except Exception as e:
            print(f"[FlightScraper] Error: {e}")
            return {"status": "failed", "reason": str(e), "tickets": []}
