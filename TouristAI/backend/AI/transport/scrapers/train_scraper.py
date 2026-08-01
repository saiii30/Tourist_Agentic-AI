import os
import sys
import json
import uuid
import tempfile
import asyncio
import subprocess
import re
from datetime import datetime

class TrainScraper:
    """Wrapper to safely execute confirmtkt_script.py in a separate process to avoid event loop issues."""

    def __init__(self):
        self.script_path = os.path.join(os.path.dirname(__file__), "confirmtkt_script.py")

    def _get_station_code(self, name: str) -> str:
        """Translate city name to standard station code."""
        cleaned_name = re.sub(r'\s+', '', name).upper()
        
        # If it's already a valid station code (2-4 uppercase letters), use it directly
        if len(cleaned_name) >= 2 and len(cleaned_name) <= 4 and cleaned_name.isalpha():
            return cleaned_name

        city_to_code = {
            'CHENNAI': 'MAS',
            'MADURAI': 'MDU',
            'COIMBATORE': 'CBE',
            'BANGALORE': 'SBC',
            'BENGALURU': 'SBC',
            'DELHI': 'NDLS',
            'NEWDELHI': 'NDLS',
            'MUMBAI': 'BCT',
            'KOLKATA': 'HWH',
            'HYDERABAD': 'HYD',
            'SALEM': 'SA',
            'TRICHY': 'TPJ',
            'TIRUCHIRAPPALLI': 'TPJ',
            'TIRUNELVELI': 'TEN',
            'KANYAKUMARI': 'CAPE',
            'PUDUCHERRY': 'PDY',
            'PONDICHERRY': 'PDY'
        }

        if cleaned_name in city_to_code:
            return city_to_code[cleaned_name]

        # Try partial match
        for city, code in city_to_code.items():
            if cleaned_name in city or city in cleaned_name:
                return code

        return cleaned_name # fallback

    def _format_date(self, date_str: str) -> str:
        """Convert YYYY-MM-DD to DD-MM-YYYY (e.g., 30-07-2026) for ConfirmTkt URL."""
        try:
            dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
            return dt.strftime("%d-%m-%Y")
        except Exception:
            dt = datetime.now() + datetime.timedelta(days=15)
            return dt.strftime("%d-%m-%Y")

    async def search(self, from_city: str, to_city: str, date: str) -> dict:
        """Run the confirmtkt script and return status and trains list."""
        if not os.path.exists(self.script_path):
            return {"status": "failed", "reason": f"Scraper script not found at {self.script_path}", "tickets": []}

        from_code = self._get_station_code(from_city)
        to_code = self._get_station_code(to_city)
        formatted_date = self._format_date(date)

        search_url = f"https://www.confirmtkt.com/rbooking/trains/from/{from_code}/to/{to_code}/{formatted_date}"
        temp_json_path = os.path.join(tempfile.gettempdir(), f"temp_trains_{uuid.uuid4().hex}.json")

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
        print(f"[TrainScraper] Running: {' '.join(cmd)}")

        try:
            proc_res = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                timeout=90
            )

            if proc_res.returncode != 0:
                print(f"[TrainScraper] Failed with exit code {proc_res.returncode}. Stderr: {proc_res.stderr}")
                return {"status": "failed", "reason": f"Subprocess exited with code {proc_res.returncode}", "tickets": []}

            if os.path.exists(temp_json_path):
                try:
                    with open(temp_json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    trains = data.get("trains", [])
                    # Inject booking URL for each train
                    for train in trains:
                        train["booking_url"] = search_url

                    return {"status": "success", "tickets": trains}
                finally:
                    try:
                        os.remove(temp_json_path)
                    except Exception:
                        pass

            return {"status": "failed", "reason": "Output JSON file not created", "tickets": []}

        except subprocess.TimeoutExpired:
            print("[TrainScraper] Scraping timed out after 90 seconds.")
            return {"status": "failed", "reason": "Scraping timed out", "tickets": []}
        except Exception as e:
            print(f"[TrainScraper] Error: {e}")
            return {"status": "failed", "reason": str(e), "tickets": []}
