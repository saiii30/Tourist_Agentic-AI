import re
from typing import List

class PackingService:
    @staticmethod
    def get_packing_tips(city: str, travel_style: str, budget: str) -> List[str]:
        city_lower = city.lower()
        style_lower = travel_style.lower()
        
        tips = [
            "Keep government IDs (Aadhaar/Passport) and travel passes ready.",
            "Bring universal chargers and a high-capacity power bank.",
            "Pack basic toiletries and a personal first-aid kit."
        ]
        
        # Cold weather check (Ooty)
        if any(w in city_lower for w in ["ooty", "shimla", "manali", "kash", "hill"]):
            tips.append("Pack warm woolens, jackets, and thermal wear for cool mornings/nights.")
            tips.append("Carry lip balm and cold cream to protect against dry wind.")
        # Beach/Warm check (Goa)
        elif any(w in city_lower for w in ["goa", "beach", "pondicherry", "kochi", "kerala"]):
            tips.append("Pack lightweight swimwear, quick-dry clothes, and sandals.")
            tips.append("Bring a good sunscreen lotion, sunglasses, and a sun hat.")
        else:
            tips.append("Pack lightweight, breathable cotton clothing suitable for warm climates.")
            
        # Temple check
        if any(w in city_lower for w in ["madurai", "chennai", "hampi", "temple", "varanasi", "tirupati"]):
            tips.append("Pack modest clothing that covers shoulders and knees for visiting sacred places.")
            tips.append("Bring slip-on shoes or sandals as footwear is not allowed inside temples.")

        # Style check
        if "adventure" in style_lower or "trek" in style_lower:
            tips.append("Pack sturdy hiking/walking shoes and insect repellent.")
            tips.append("Bring a lightweight rain jacket or windbreaker.")
        elif "family" in style_lower:
            tips.append("Carry kid-friendly snacks and wet wipes for convenience.")
            
        return tips

    @staticmethod
    def get_packing_checklist(city: str, travel_style: str, budget: str) -> List[dict]:
        city_lower = city.lower()
        style_lower = travel_style.lower()
        
        items = [
            {"id": "p-1", "name": "Travel tickets & booking passes", "checked": True},
            {"id": "p-2", "name": "Aadhaar Card / Government ID card", "checked": True},
            {"id": "p-3", "name": "Mobile charger & Power bank", "checked": False},
            {"id": "p-4", "name": "Basic medicine kit (painkillers, band-aids)", "checked": False}
        ]
        
        idx = 5
        if any(w in city_lower for w in ["ooty", "hill"]):
            items.append({"id": f"p-{idx}", "name": "Sweater / Thermal jacket", "checked": False})
            idx += 1
            items.append({"id": f"p-{idx}", "name": "Umbrella or windbreaker", "checked": False})
            idx += 1
        elif any(w in city_lower for w in ["goa", "beach"]):
            items.append({"id": f"p-{idx}", "name": "Sunscreen lotion (SPF 50+)", "checked": False})
            idx += 1
            items.append({"id": f"p-{idx}", "name": "Beach slippers / Sunglasses", "checked": False})
            idx += 1
            items.append({"id": f"p-{idx}", "name": "Swimwear / Light clothing", "checked": False})
            idx += 1
        else:
            items.append({"id": f"p-{idx}", "name": "Breathable cotton outfits", "checked": False})
            idx += 1
            items.append({"id": f"p-{idx}", "name": "Comfortable walking shoes", "checked": False})
            idx += 1
            
        if "adventure" in style_lower:
            items.append({"id": f"p-{idx}", "name": "Insect repellent spray", "checked": False})
            idx += 1
            items.append({"id": f"p-{idx}", "name": "Trekking shoes", "checked": False})
            idx += 1
        elif "shopping" in style_lower:
            items.append({"id": f"p-{idx}", "name": "Reusable shopping bags", "checked": False})
            idx += 1
            
        return items
