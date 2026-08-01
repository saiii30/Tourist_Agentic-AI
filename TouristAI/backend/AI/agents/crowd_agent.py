# backend/AI/agents/crowd_agent.py
import sys
import os
from typing import Dict, Any, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.crowd_service import crowd_service
from rag.service import rag_service

def crowd_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crowd Intelligence Agent v2.0 for TouristAI.
    Combines:
    1. Official RAG data (festivals, holiday calendars, government advisories)
    2. Live API data (weather forecast, traffic, business hours)
    3. Historical footfall analytics (weekend vs weekday, hourly rush curves)
    
    Produces:
    - Optimal arrival recommendations for itinerary scheduling
    - Map density color codes (🟢 Low, 🟡 Moderate, 🟠 Busy, 🔴 Very Busy)
    - Budget surge/wait time impacts
    """
    print("Executing Crowd Intelligence Agent...")

    city = state.get("city", "Madurai")
    if city == "None" or not city:
        city = "Madurai"

    date_str = state.get("travel_date") or None
    weather_info = state.get("weather_data", {})
    is_raining = "rain" in str(weather_info.get("description", "")).lower()

    # 1. Query RAG for official festival & holiday advisories for this city
    rag_festival_info = ""
    try:
        rag_res = rag_service.query_rag(
            f"festivals holidays crowd advisory for {city}",
            agent_name="CrowdAgent",
            city=city,
            top_k=2
        )
        if rag_res.get("has_knowledge") and rag_res.get("context_text"):
            rag_festival_info = rag_res["context_text"]
    except Exception as e:
        print(f"[CROWD AGENT] RAG lookup warning: {e}")

    # Sample key destinations for analysis
    sample_destinations = [
        {"name": f"Meenakshi Amman Temple", "category": "temple"},
        {"name": f"Tirumalai Nayakkar Palace", "category": "monument"},
        {"name": f"Gandhi Memorial Museum", "category": "museum"},
        {"name": f"Local Central Bazaar", "category": "market"}
    ]

    analysis_results = []
    map_crowd_levels = {}
    optimal_schedule = {}

    for dest in sample_destinations:
        pred = crowd_service.predict_crowd(
            destination=dest["name"],
            city=city,
            date_str=date_str,
            time_str="10:00",
            category=dest["category"]
        )

        # Weather adjustment: rain increases indoor crowd and reduces outdoor crowd
        if is_raining:
            if dest["category"] in ["temple", "museum"]:
                pred["current_crowd_percentage"] = min(98, pred["current_crowd_percentage"] + 15)
                pred["advisory"] += " ☔ Rain expected: Indoor tourist footfall boosted."
            else:
                pred["current_crowd_percentage"] = max(10, pred["current_crowd_percentage"] - 20)

        # Map marker color mapping
        pct = pred["current_crowd_percentage"]
        if pct < 35:
            color_token = "emerald"
            label = "Low Crowd"
        elif pct < 70:
            color_token = "amber"
            label = "Moderate"
        elif pct < 85:
            color_token = "orange"
            label = "Busy"
        else:
            color_token = "rose"
            label = "Very Busy"

        map_crowd_levels[dest["name"]] = {
            "percentage": pct,
            "color": color_token,
            "label": label,
            "badge": pred["badge"]
        }

        optimal_schedule[dest["name"]] = {
            "recommended_arrival": pred["recommended_window"],
            "expected_crowd": pred["crowd_level"],
            "advisory": pred["advisory"]
        }

        analysis_results.append(pred)

    summary_text = (
        f"**Crowd Intelligence Report for {city.title()}**\n\n"
        f"- **Festival & Holiday Context**: {rag_festival_info[:150] if rag_festival_info else 'Standard seasonal footfall'}\n"
        f"- **Recommended Peak Avoidance Strategy**: Visit major temples & heritage spots before 08:30 AM to skip 2+ hour queues.\n"
    )

    return {
        "crowd_data": {
            "city": city,
            "summary": summary_text,
            "destinations_analysis": analysis_results,
            "map_crowd_levels": map_crowd_levels,
            "optimal_schedule": optimal_schedule,
            "budget_surge_factor": 1.25 if any(p["current_crowd_percentage"] > 75 for p in analysis_results) else 1.0
        }
    }
