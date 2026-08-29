import os
import sys
import json
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Adjust path to import correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.postgres import PostgresDatabase
from repositories.trip_repository import TripRepository
from models.itinerary import Trip, ItineraryItem
from services.packing_service import PackingService
from services.budget_service import BudgetService
from services.emergency_service import EmergencyService
from services.osrm_service import geocode_place
from rag_service import client

class TripService:
    def __init__(self) -> None:
        self.repo = TripRepository()
        self.db_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agents", "locations_data.json")

    def get_cached_trip(self, city: str, days: int, budget: str, travel_style: str) -> Optional[Dict[str, Any]]:
        """
        Check SQLite database for an existing matching trip.
        """
        conn = PostgresDatabase.get_connection()
        import psycopg2.extras
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Look for matching trip parameters
        cursor.execute(
            "SELECT * FROM trips WHERE LOWER(city) = %s AND days = %s AND LOWER(budget) = %s AND LOWER(travel_style) = %s",
            (city.strip().lower(), days, budget.strip().lower(), travel_style.strip().lower())
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row:
            return None
            
        trip_data = dict(row)
        trip_id = trip_data["trip_id"]
        
        # Retrieve its itinerary items
        items = self.repo.get_itinerary_items(trip_id)
        if not items:
            return None
            
        # Build structured itinerary dictionary expected by frontend
        itinerary = {}
        for item in items:
            day_str = str(item.day)
            if day_str not in itinerary:
                itinerary[day_str] = []
                
            start = item.start_time or "09:00"
            try:
                time_str = datetime.strptime(start, "%H:%M").strftime("%I:%M %p")
            except:
                time_str = start

            item_lat, item_lng = geocode_place(item.location or item.activity, city)
            itinerary[day_str].append({
                "id": f"cached-act-{item.day}-{len(itinerary[day_str])}",
                "title": item.activity,
                "time": time_str,
                "duration": f"{item.start_time} - {item.end_time}",
                "category": item.category,
                "rating": 4.5,
                "entryFee": "See Notes",
                "description": item.notes or "",
                "location": item.location or "",
                "image": self._get_image_for_category(item.category, city),
                "latitude": item_lat,
                "longitude": item_lng,
                "travel_time": item.travel_time,
                "transport": item.transport,
                "distance": item.distance
            })

        # Enrich with other services
        packing_tips = PackingService.get_packing_tips(city, travel_style, budget)
        packing_checklist = PackingService.get_packing_checklist(city, travel_style, budget)
        budget_summary = BudgetService.calculate_budget_summary(city, days, budget)
        emergency_contacts = EmergencyService.get_emergency_contacts(city)
        # Try to load hotels/restaurants from saved trip details in database
        hotels = None
        restaurants = None
        try:
            db_details = self.repo.get_trip_details(trip_id)
            if db_details:
                hotels = db_details.get("hotels")
                restaurants = db_details.get("restaurants")
        except Exception as e:
            print(f"Error loading saved trip details for cached hotels/restaurants: {e}")
            
        if not hotels:
            hotels = self.get_structured_hotels(city, budget)
        if not restaurants:
            restaurants = self.get_structured_restaurants(city, budget)

        return {
            "status": "success",
            "trip": {
                "trip_id": trip_id,
                "city": city.title(),
                "duration": days,
                "budget": budget,
                "travel_style": travel_style,
                "travelers": trip_data.get("travelers", 1),
                "weather_summary": budget_summary.get("weather_summary", f"Weather forecast for {city.title()}"),
                "packing": packing_tips,
                "packing_checklist": packing_checklist,
                "emergency": emergency_contacts,
                "budget_summary": budget_summary,
                "hotels": hotels,
                "restaurants": restaurants,
                "itinerary": itinerary,
                "calendar": {
                    "saved": trip_data.get("status") == "saved",
                    "synced": trip_data.get("status") == "synced"
                }
            },
            "metadata": {
                "source": "sqlite",
                "generated_by": "trip_repository",
                "cached": True,
                "generated_at": trip_data.get("created_at")
            }
        }

    def get_structured_hotels(self, city: str, budget: str) -> List[Dict[str, Any]]:
        city_clean = city.strip().lower()
        budget_clean = budget.strip().lower()
        
        budget_val = "Low"
        if "moderate" in budget_clean:
            budget_val = "Moderate"
        elif "luxury" in budget_clean:
            budget_val = "Luxury"
            
        hotels_mapped = []
        
        # Load from locations_data.json
        if os.path.exists(self.db_json_path):
            try:
                with open(self.db_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                city_data = data.get(city_clean)
                if city_data and "hotels" in city_data:
                    matched = [h for h in city_data["hotels"] if h.get("budget") == budget_val]
                    if len(matched) < 2:
                        others = [h for h in city_data["hotels"] if h.get("budget") != budget_val]
                        matched = (matched + others)[:2]
                        
                    for idx, h in enumerate(matched):
                        price_num = 3000
                        try:
                            # Extract price digits
                            price_digits = re.findall(r'\d+', h["price"].replace(",", ""))
                            if price_digits:
                                price_num = int(price_digits[0])
                        except:
                            pass
                            
                        hotels_mapped.append({
                            "id": f"hotel-{idx}",
                            "name": h["name"],
                            "image": self._get_hotel_image(idx, city_clean),
                            "rating": 4.5 + (idx * 0.2),
                            "pricePerNight": price_num,
                            "amenities": h.get("features", ["Free Wi-Fi", "Room Service"]),
                            "distanceFromCenter": "1.2 km from City Center",
                            "bookingUrl": "https://booking.com"
                        })
            except Exception as e:
                print(f"Error loading hotels: {e}")
                
        # If no hotels generated (e.g. uncatalogued city), call LLM to generate realistic ones
        if not hotels_mapped:
            hotels_mapped = self._generate_llm_hotels(city, budget_val)
            
        return self._with_coordinates(hotels_mapped, city)

    def get_structured_restaurants(self, city: str, budget: str) -> List[Dict[str, Any]]:
        city_clean = city.strip().lower()
        budget_clean = budget.strip().lower()
        
        budget_val = "Low"
        if "moderate" in budget_clean:
            budget_val = "Moderate"
        elif "luxury" in budget_clean:
            budget_val = "Luxury"
            
        rests_mapped = []
        
        # Load from locations_data.json
        if os.path.exists(self.db_json_path):
            try:
                with open(self.db_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                city_data = data.get(city_clean)
                if city_data and "restaurants" in city_data:
                    matched = [r for r in city_data["restaurants"] if r.get("budget") == budget_val]
                    if len(matched) < 3:
                        others = [r for r in city_data["restaurants"] if r.get("budget") != budget_val]
                        matched = (matched + others)[:3]
                        
                    for idx, r in enumerate(matched):
                        rests_mapped.append({
                            "id": f"rest-{idx}",
                            "name": r["name"],
                            "image": self._get_food_image(idx),
                            "rating": 4.6 + (idx * 0.1),
                            "cuisine": r.get("cuisine", "Local Cuisine"),
                            "priceTier": "$$$" if budget_val == "Moderate" else ("$$$$" if budget_val == "Luxury" else "$$"),
                            "distanceFromHotel": "0.6 km",
                            "reservationAvailable": idx % 2 == 0
                        })
            except Exception as e:
                print(f"Error loading restaurants: {e}")
                
        # If no restaurants generated (uncatalogued city), call LLM to generate realistic ones
        if not rests_mapped:
            rests_mapped = self._generate_llm_restaurants(city, budget_val)
            
        return self._with_coordinates(rests_mapped, city)

    def get_structured_attractions(self, city: str, budget: str = "Moderate") -> List[Dict[str, Any]]:
        city_clean = city.strip().lower()
        attractions_mapped = []

        if os.path.exists(self.db_json_path):
            try:
                with open(self.db_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                city_data = data.get(city_clean)
                source_attractions = city_data.get("attractions", []) if city_data else []
                for idx, attraction in enumerate(source_attractions[:8]):
                    name = attraction.get("name") or attraction.get("title") or f"{city.title()} Attraction {idx + 1}"
                    attractions_mapped.append({
                        "attraction_id": attraction.get("attraction_id") or attraction.get("id") or f"attr-{idx}",
                        "name": name,
                        "address": attraction.get("address") or f"{city.title()}",
                        "description": attraction.get("description") or attraction.get("notes") or f"Popular place to visit in {city.title()}.",
                        "rating": attraction.get("rating") or 4.5,
                        "image": attraction.get("image") or self._get_image_for_category("Sightseeing", city),
                        "latitude": attraction.get("latitude") or attraction.get("lat"),
                        "longitude": attraction.get("longitude") or attraction.get("lng"),
                    })
            except Exception as e:
                print(f"Error loading attractions: {e}")

        if not attractions_mapped:
            attractions_mapped = self._generate_llm_attractions(city, budget)

        return self._with_coordinates(attractions_mapped, city)

    def _with_coordinates(self, items: List[Dict[str, Any]], city: str) -> List[Dict[str, Any]]:
        for item in items:
            lat = item.get("latitude") or item.get("lat")
            lng = item.get("longitude") or item.get("lng")
            if lat is not None and lng is not None:
                try:
                    item["latitude"] = float(lat)
                    item["longitude"] = float(lng)
                    continue
                except (TypeError, ValueError):
                    pass

            name = item.get("name") or item.get("title") or city
            plat, plng = geocode_place(name, city)
            item["latitude"] = plat
            item["longitude"] = plng
        return items

    def _get_hotel_image(self, idx: int, city: str) -> str:
        images = [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Indian_hotel.jpg/400px-Indian_hotel.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Hotel_room.jpg/400px-Hotel_room.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2b/Hotel_lobby.jpg/400px-Hotel_lobby.jpg"
        ]
        return images[idx % len(images)]

    def _get_food_image(self, idx: int) -> str:
        images = [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Indian_dinner.jpg/400px-Indian_dinner.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Indian_cuisine.jpg/400px-Indian_cuisine.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Indian_breakfast.jpg/400px-Indian_breakfast.jpg"
        ]
        return images[idx % len(images)]

    def _get_image_for_category(self, category: str, city: str) -> str:
        cat_lower = category.lower()
        if "food" in cat_lower or "restaurant" in cat_lower:
            return "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Indian_dinner.jpg/400px-Indian_dinner.jpg"
        elif "hotel" in cat_lower or "accommodation" in cat_lower or "stay" in cat_lower:
            return "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Indian_hotel.jpg/400px-Indian_hotel.jpg"
        elif "nature" in cat_lower or "beach" in cat_lower or "waterfall" in cat_lower:
            return "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Indian_park.jpg/400px-Indian_park.jpg"
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Tourism_in_India.jpg/400px-Tourism_in_India.jpg"

    def _generate_llm_hotels(self, city: str, budget_val: str) -> List[Dict[str, Any]]:
        prompt = (
            f"Generate a JSON list of 2 realistic hotel recommendations for a traveler visiting {city} "
            f"on a {budget_val} budget.\n"
            "Return strictly a valid JSON array matching this format and nothing else:\n"
            "[\n"
            "  {\n"
            "    \"id\": \"hotel-1\",\n"
            "    \"name\": \"Hotel Name\",\n"
            "    \"image\": \"https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=400&q=80\",\n"
            "    \"rating\": 4.5,\n"
            "    \"pricePerNight\": 3500,\n"
            "    \"amenities\": [\"Free Wi-Fi\", \"Swimming Pool\"],\n"
            "    \"distanceFromCenter\": \"1.0 km from city center\",\n"
            "    \"bookingUrl\": \"https://booking.com\"\n"
            "  }\n"
            "]\n"
            "Only return raw valid JSON. Do not include markdown code block backticks."
        )
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            content = response.choices[0].message.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            if "[" in content:
                content = content[content.find("["):content.rfind("]")+1]
            return json.loads(content)
        except Exception as e:
            print(f"Error generating LLM hotels for {city}: {e}")
            price_night = 4500 if budget_val == "Moderate" else (12000 if budget_val == "Luxury" else 1500)
            return [
                {
                    "id": "hotel-fallback-1",
                    "name": f"Comfort Inn {city.title()}",
                    "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=400&q=80",
                    "rating": 4.5,
                    "pricePerNight": price_night,
                    "amenities": ["Free Wi-Fi", "Room Service"],
                    "distanceFromCenter": "1.5 km from Center",
                    "bookingUrl": "https://booking.com"
                }
            ]

    def _generate_llm_restaurants(self, city: str, budget_val: str) -> List[Dict[str, Any]]:
        prompt = (
            f"Generate a JSON list of 3 realistic restaurant/dining recommendations for a traveler visiting {city} "
            f"on a {budget_val} budget.\n"
            "Return strictly a valid JSON array matching this format and nothing else:\n"
            "[\n"
            "  {\n"
            "    \"id\": \"rest-1\",\n"
            "    \"name\": \"Restaurant Name\",\n"
            "    \"image\": \"https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=400&q=80\",\n"
            "    \"rating\": 4.6,\n"
            "    \"cuisine\": \"Traditional\",\n"
            "    \"priceTier\": \"$$\",\n"
            "    \"distanceFromHotel\": \"0.8 km\",\n"
            "    \"reservationAvailable\": true\n"
            "  }\n"
            "]\n"
            "Only return raw valid JSON. Do not include markdown code block backticks."
        )
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            content = response.choices[0].message.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            if "[" in content:
                content = content[content.find("["):content.rfind("]")+1]
            return json.loads(content)
        except Exception as e:
            print(f"Error generating LLM restaurants for {city}: {e}")
            tier = "$$$" if budget_val == "Moderate" else ("$$$$" if budget_val == "Luxury" else "$$")
            return [
                {
                    "id": "rest-fallback-1",
                    "name": f"The Local Bistro {city.title()}",
                    "image": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=400&q=80",
                    "rating": 4.6,
                    "cuisine": "Multicuisine & Local",
                    "priceTier": tier,
                    "distanceFromHotel": "0.9 km",
                    "reservationAvailable": False
                }
            ]

    def _generate_llm_attractions(self, city: str, budget_val: str) -> List[Dict[str, Any]]:
        prompt = (
            f"Generate a JSON list of 6 realistic tourist attractions or experiences for a traveler visiting {city} "
            f"on a {budget_val} budget.\n"
            "Return strictly a valid JSON array matching this format and nothing else:\n"
            "[\n"
            "  {\n"
            "    \"attraction_id\": \"attr-1\",\n"
            "    \"name\": \"Attraction Name\",\n"
            "    \"address\": \"Area or full address\",\n"
            "    \"description\": \"One concise sentence explaining why to visit\",\n"
            "    \"rating\": 4.5,\n"
            "    \"category\": \"Sightseeing\"\n"
            "  }\n"
            "]\n"
            "Only return raw valid JSON. Do not include markdown code block backticks."
        )
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            content = response.choices[0].message.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            if "[" in content:
                content = content[content.find("["):content.rfind("]")+1]
            data = json.loads(content)
            mapped = []
            for idx, item in enumerate(data):
                name = item.get("name") or f"{city.title()} Attraction {idx + 1}"
                mapped.append({
                    "attraction_id": item.get("attraction_id") or item.get("id") or f"attr-llm-{idx + 1}",
                    "name": name,
                    "address": item.get("address") or f"{name}, {city.title()}",
                    "description": item.get("description") or f"A recommended stop for travelers exploring {city.title()}.",
                    "rating": item.get("rating") or 4.4,
                    "category": item.get("category") or "Sightseeing",
                    "image": self._get_image_for_category(item.get("category", "Sightseeing"), city),
                })
            return mapped
        except Exception as e:
            print(f"Error generating LLM attractions for {city}: {e}")
            seed_names = [
                f"{city.title()} Scenic View Point",
                f"{city.title()} Local Market",
                f"{city.title()} Heritage Walk",
                f"{city.title()} Nature Spot",
                f"{city.title()} Cultural Center",
                f"{city.title()} Evening Viewpoint",
            ]
            return [
                {
                    "attraction_id": f"attr-fallback-{idx + 1}",
                    "name": name,
                    "address": f"{name}, {city.title()}",
                    "description": f"A recommended stop for travelers exploring {city.title()}.",
                    "rating": 4.4,
                    "category": "Sightseeing",
                    "image": self._get_image_for_category("Sightseeing", city),
                }
                for idx, name in enumerate(seed_names)
            ]


_trip_service_singleton = TripService()


def get_structured_hotels(city: str, budget: str) -> List[Dict[str, Any]]:
    return _trip_service_singleton.get_structured_hotels(city, budget)


def get_structured_restaurants(city: str, budget: str) -> List[Dict[str, Any]]:
    return _trip_service_singleton.get_structured_restaurants(city, budget)


def get_structured_attractions(city: str, budget: str = "Moderate") -> List[Dict[str, Any]]:
    return _trip_service_singleton.get_structured_attractions(city, budget)
