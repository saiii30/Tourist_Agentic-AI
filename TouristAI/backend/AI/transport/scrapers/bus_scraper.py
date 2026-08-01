import os
import sys
import json
import uuid
import tempfile
import asyncio
import subprocess
from datetime import datetime

class BusScraper:
    """Wrapper to safely execute redbus_script.py in a separate process to avoid event loop issues."""

    def __init__(self):
        self.script_path = os.path.join(os.path.dirname(__file__), "redbus_script.py")

    def _format_date(self, date_str: str) -> str:
        """Convert YYYY-MM-DD to DD-MMM-YYYY (e.g., 30-Jul-2026) for redBus doj parameter."""
        try:
            dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
            # Format: e.g. 30-Jul-2026
            return dt.strftime("%d-%b-%Y")
        except Exception:
            # Fallback: 15 days from now
            dt = datetime.now() + datetime.timedelta(days=15)
            return dt.strftime("%d-%b-%Y")

    async def search(self, from_city: str, to_city: str, date: str) -> dict:
        """Run the redbus script and return status and schedules."""
        if not os.path.exists(self.script_path):
            return {"status": "failed", "reason": f"Scraper script not found at {self.script_path}", "tickets": []}

        formatted_date = self._format_date(date)
        clean_from = from_city.lower().strip().replace(" ", "-")
        clean_to = to_city.lower().strip().replace(" ", "-")
        
        search_url = f"https://www.redbus.in/bus-tickets/{clean_from}-to-{clean_to}?doj={formatted_date}"
        temp_json_path = os.path.join(tempfile.gettempdir(), f"temp_buses_{uuid.uuid4().hex}.json")
        
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
        print(f"[BusScraper] Running: {' '.join(cmd)}")

        try:
            # Run in a thread pool to avoid blocking FastAPI's event loop
            proc_res = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                timeout=90
            )
            
            if proc_res.returncode != 0:
                print(f"[BusScraper] Failed with exit code {proc_res.returncode}. Stderr: {proc_res.stderr}")
                return {"status": "failed", "reason": f"Subprocess exited with code {proc_res.returncode}", "tickets": []}

            if os.path.exists(temp_json_path):
                try:
                    with open(temp_json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    tickets = data.get("buses", [])
                    # Inject booking URL for each ticket
                    for ticket in tickets:
                        ticket["booking_url"] = search_url

                    return {"status": "success", "tickets": tickets}
                finally:
                    try:
                        os.remove(temp_json_path)
                    except Exception:
                        pass
            
            return {"status": "failed", "reason": "Output JSON file not created", "tickets": []}
            
        except subprocess.TimeoutExpired:
            print("[BusScraper] Scraping timed out after 90 seconds.")
            return {"status": "failed", "reason": "Scraping timed out", "tickets": []}
        except Exception as e:
            print(f"[BusScraper] Error: {e}")
            return {"status": "failed", "reason": str(e), "tickets": []}
