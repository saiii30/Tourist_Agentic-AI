import sys
import os
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

# Adjust path to import correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.itinerary import ItineraryItem, Trip
from rag_service import client

class ItineraryService:
    def __init__(self) -> None:
        self.model = "openai/gpt-oss-20b"

    def parse_markdown_to_items(self, markdown_text: str) -> List[ItineraryItem]:
        """
        Parses Markdown itinerary into structured ItineraryItem records using LLM.
        """
        prompt = (
            "Analyze the following travel itinerary markdown and extract all activities as a structured JSON list. "
            "For each activity/event, extract:\n"
            "- day: Integer representing the day of the activity (1-indexed)\n"
            "- start_time: Start time in 24h format (HH:MM, e.g. '09:00', '13:30')\n"
            "- end_time: End time in 24h format (HH:MM, e.g. '12:00', '17:00')\n"
            "- activity: Short name of the activity/attraction\n"
            "- location: Location or address where the activity happens\n"
            "- category: One of 'Sightseeing', 'Food', 'Shopping', 'Relaxation', 'Transit'\n"
            "- restaurant: Name of the restaurant if it's a dining spot, or null\n"
            "- hotel: Name of the hotel if it's check-in/stay related, or null\n"
            "- notes: Brief description or details of the activity\n\n"
            "Return the output strictly in the following JSON format and nothing else:\n"
            "[\n"
            "  {\n"
            "    \"day\": 1,\n"
            "    \"start_time\": \"09:00\",\n"
            "    \"end_time\": \"12:00\",\n"
            "    \"activity\": \"Activity Name\",\n"
            "    \"location\": \"Location Name\",\n"
            "    \"category\": \"Sightseeing\",\n"
            "    \"restaurant\": null,\n"
            "    \"hotel\": \"Treebo Select Vagator\",\n"
            "    \"notes\": \"Details about the place\"\n"
            "  }\n"
            "]\n\n"
            "Do not include any explanation, backticks (like ```json), or markdown formatting. Output ONLY a valid JSON list.\n\n"
            f"Itinerary Markdown:\n{markdown_text}"
        )
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            content = response.choices[0].message.content.strip()
            
            # Clean LLM response to get pure JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            if "[" in content:
                content = content[content.find("["):content.rfind("]")+1]
                
            data = json.loads(content)
            return [ItineraryItem(**item) for item in data]
        except Exception as e:
            print(f"Error parsing markdown itinerary: {e}")
            return []

    def modify_itinerary(self, existing_items: List[ItineraryItem], modification_request: str) -> List[ItineraryItem]:
        """
        Modifies specific parts of the itinerary based on natural language, preserving unchanged elements.
        """
        existing_json = json.dumps([item.dict() for item in existing_items], indent=2)
        prompt = (
            "You are a structured travel itinerary modification engine. "
            "You must modify the existing travel itinerary based on the user's natural language request. "
            "Follow these rules strictly:\n"
            "1. Modify ONLY the parts of the itinerary that are affected by the request. Keep all other activities exactly the same (do not change their names, locations, categories, times, or notes).\n"
            "2. If an activity is replaced, remove the old activity and insert the new one in the same time slot/day.\n"
            "3. Ensure the times (start_time, end_time) are consistent and do not overlap.\n"
            "4. Return the updated list of activities strictly matching the input JSON schema. Output ONLY a valid JSON list. No explanation, no backticks, no markdown formatting.\n\n"
            f"Existing Itinerary JSON:\n{existing_json}\n\n"
            f"User's Modification Request: '{modification_request}'"
        )
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            if "[" in content:
                content = content[content.find("["):content.rfind("]")+1]
                
            data = json.loads(content)
            return [ItineraryItem(**item) for item in data]
        except Exception as e:
            print(f"Error modifying itinerary: {e}")
            # Return original if modification failed
            return existing_items

    def regenerate_itinerary(self, trip: Trip, previous_items: List[ItineraryItem]) -> List[ItineraryItem]:
        """
        Generates a different itinerary for the same parameters, avoiding previous attractions/restaurants.
        """
        previous_json = json.dumps([item.dict() for item in previous_items], indent=2)
        prompt = (
            f"Generate a brand new, highly realistic {trip.days}-day travel itinerary for {trip.city}.\n"
            f"Travel parameters to respect:\n"
            f"- Budget Level: {trip.budget}\n"
            f"- Travelers: {trip.travelers}\n"
            f"- Travel Style: {trip.travel_style}\n"
            f"- Special Interests: {trip.interests}\n\n"
            "Critical Instruction:\n"
            "Avoid repeating the activities, hotels, restaurants, or locations from the previous itinerary if possible. Generate an alternative plan.\n\n"
            f"Previous Itinerary (Avoid repeating these):\n{previous_json}\n\n"
            "Return the response strictly as a JSON array of itinerary items matching this schema:\n"
            "[\n"
            "  {\n"
            "    \"day\": 1,\n"
            "    \"start_time\": \"09:00\",\n"
            "    \"end_time\": \"12:00\",\n"
            "    \"activity\": \"Activity Name\",\n"
            "    \"location\": \"Location Name\",\n"
            "    \"category\": \"Sightseeing\",\n"
            "    \"restaurant\": null,\n"
            "    \"hotel\": \"Alternative Hotel Name\",\n"
            "    \"notes\": \"Details about the alternative attraction\"\n"
            "  }\n"
            "]\n\n"
            "Output ONLY valid JSON. No explanation, no backticks, no markdown."
        )
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7 # slightly higher temp for creativity/variation
            )
            content = response.choices[0].message.content.strip()
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            if "[" in content:
                content = content[content.find("["):content.rfind("]")+1]
                
            data = json.loads(content)
            return [ItineraryItem(**item) for item in data]
        except Exception as e:
            print(f"Error regenerating itinerary: {e}")
            return previous_items
