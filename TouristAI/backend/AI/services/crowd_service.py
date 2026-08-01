# backend/AI/services/crowd_service.py
import datetime
from typing import Dict, Any, List

class CrowdPredictionService:
    """
    AI Crowd Prediction Engine for TouristAI.
    Blends historical tourism footfall, holiday/festival calendars, day of week,
    and hour of day to recommend less crowded visiting windows.
    """

    # Known regional peak festival & holiday dates (YYYY-MM-DD or MM-DD ranges)
    FESTIVAL_CALENDAR = {
        "madurai": [
            {"name": "Chithirai Brahmotsavam Festival", "start": "04-15", "end": "04-30", "boost": 40},
            {"name": "Float Festival (Teppothsavam)", "start": "01-15", "end": "01-25", "boost": 35},
            {"name": "Pongal Harvest Holidays", "start": "01-14", "end": "01-18", "boost": 30},
            {"name": "Diwali Festival Holidays", "start": "10-20", "end": "11-05", "boost": 35},
        ],
        "ooty": [
            {"name": "Ooty Summer Festival & Flower Show", "start": "05-01", "end": "05-31", "boost": 45},
            {"name": "Pujas & Dussehra Holidays", "start": "10-01", "end": "10-15", "boost": 35},
        ],
        "chennai": [
            {"name": "Chennai Music & Dance Season", "start": "12-15", "end": "01-15", "boost": 30},
            {"name": "Kapaaleeshwarar Panguni Uthiram", "start": "03-15", "end": "03-25", "boost": 40},
        ]
    }

    # Standard hourly crowd distribution baseline by category (0-23 hours)
    HOURLY_BASELINES = {
        "temple": [
            10, 5, 5, 10, 25, 45, 30, 40, 65, 85, 90, 85,  # 00:00 - 11:00 (Morning darshan peak 09:00-11:00)
            30, 20, 25, 40, 60, 85, 95, 90, 75, 40, 20, 10   # 12:00 - 23:00 (Evening darshan peak 17:00-19:00)
        ],
        "monument": [
            5, 0, 0, 0, 0, 10, 20, 30, 45, 65, 80, 85,     # 00:00 - 11:00
            80, 75, 70, 75, 80, 60, 30, 15, 10, 5, 0, 0      # 12:00 - 23:00
        ],
        "nature": [
            0, 0, 0, 0, 5, 20, 40, 50, 60, 70, 75, 80,     # 00:00 - 11:00
            80, 75, 75, 80, 85, 70, 40, 20, 10, 0, 0, 0      # 12:00 - 23:00
        ],
        "market": [
            0, 0, 0, 0, 0, 0, 10, 20, 35, 50, 65, 75,      # 00:00 - 11:00
            75, 70, 70, 75, 85, 95, 95, 90, 75, 50, 20, 5    # 12:00 - 23:00
        ]
    }

    @classmethod
    def predict_crowd(
        cls,
        destination: str,
        city: str = "Madurai",
        date_str: str = None,
        time_str: str = "10:00",
        category: str = "temple"
    ) -> Dict[str, Any]:
        """
        Predicts crowd percentage, status level, hourly trend, and best quiet visiting window.
        """
        norm_city = (city or "Madurai").strip().lower()
        norm_cat = "temple" if any(w in destination.lower() for w in ["temple", "koyil", "church", "mosque"]) else "monument"
        if any(w in category.lower() for w in ["park", "garden", "lake", "falls"]):
            norm_cat = "nature"
        elif any(w in category.lower() for w in ["bazaar", "market", "mall", "shop"]):
            norm_cat = "market"

        # Parse date
        try:
            target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.datetime.now()
        except Exception:
            target_date = datetime.datetime.now()

        # Parse target hour
        try:
            target_hour = int(time_str.split(":")[0])
        except Exception:
            target_hour = 10

        target_hour = max(0, min(23, target_hour))

        # Base hourly profile
        baseline = list(cls.HOURLY_BASELINES.get(norm_cat, cls.HOURLY_BASELINES["monument"]))

        # 1. Weekend Factor
        is_weekend = target_date.weekday() in [5, 6]
        weekend_boost = 15 if is_weekend else 0

        # 2. Regional Festival Boost
        mm_dd = target_date.strftime("%m-%d")
        festival_boost = 0
        active_festival = None

        city_festivals = cls.FESTIVAL_CALENDAR.get(norm_city, [])
        for fest in city_festivals:
            if fest["start"] <= mm_dd <= fest["end"]:
                festival_boost = fest["boost"]
                active_festival = fest["name"]
                break

        # Generate modified 24-hour forecast
        hourly_forecast = []
        for h in range(24):
            base_p = baseline[h]
            if base_p > 0:
                adjusted = min(98, base_p + weekend_boost + festival_boost)
            else:
                adjusted = 0
            hourly_forecast.append(int(adjusted))

        current_percentage = hourly_forecast[target_hour]

        # Determine Crowd Level
        if current_percentage < 35:
            level = "Low Crowd"
            status_color = "emerald"
            badge = "Quiet & Easy Access"
        elif current_percentage < 70:
            level = "Moderate Crowd"
            status_color = "amber"
            badge = "Moderate Wait Times"
        elif current_percentage < 85:
            level = "Heavy Rush"
            status_color = "rose"
            badge = "High Crowd Alert"
        else:
            level = "Extreme Peak Rush"
            status_color = "purple"
            badge = "Festival Peak Lines"

        # Calculate best quiet window (lowest crowd hours between 06:00 and 18:00)
        daytime_hours = [(h, hourly_forecast[h]) for h in range(6, 19) if hourly_forecast[h] > 0]
        if daytime_hours:
            daytime_hours.sort(key=lambda x: x[1])
            best_h, best_p = daytime_hours[0]
            
            def fmt_h(h_num):
                ampm = "AM" if h_num < 12 else "PM"
                h12 = h_num if h_num <= 12 else h_num - 12
                h12 = 12 if h12 == 0 else h12
                return f"{h12:02d}:00 {ampm}"

            recommended_window = f"{fmt_h(best_h)} - {fmt_h(best_h + 1)} (Est. {best_p}% crowd)"
        else:
            recommended_window = "06:00 AM - 08:30 AM (Early Morning)"

        # Generate advisory message
        advisory = f"Ideal time to visit {destination} is during early morning hours to skip queues."
        if active_festival:
            advisory = f"⚠️ {active_festival} is active! Visiting around {recommended_window} saves up to 2 hours in line."
        elif is_weekend:
            advisory = f"Weekend tourist influx detected. Recommended visiting window: {recommended_window}."

        return {
            "destination": destination,
            "city": city.title(),
            "date": target_date.strftime("%Y-%m-%d"),
            "target_hour": target_hour,
            "current_crowd_percentage": current_percentage,
            "crowd_level": level,
            "status_color": status_color,
            "badge": badge,
            "recommended_window": recommended_window,
            "active_festival": active_festival,
            "is_weekend": is_weekend,
            "advisory": advisory,
            "hourly_forecast": hourly_forecast
        }

crowd_service = CrowdPredictionService()
