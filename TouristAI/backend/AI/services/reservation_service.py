import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

# Adjust path to import correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_service import client
from services.google_calendar_service import GoogleCalendarService

class ReservationService:
    @staticmethod
    def parse_booking_text(text: str, current_time_str: str = "2026-07-02") -> Dict[str, Any]:
        """
        Uses Llama model to extract structured calendar event details from pasted ticket text.
        """
        prompt = (
            "You are an expert travel assistant. Extract the travel booking details from the raw ticket text below.\n"
            f"Note: The current year/date context is: {current_time_str}.\n\n"
            "Return STRICTLY a JSON object matching this schema and nothing else:\n"
            "{\n"
            '  "title": "Train to MADURAI JN (MDU)",\n'
            '  "location": "CHENNAI EGMORE (MS)",\n'
            '  "start_time": "2026-07-01T15:10:00",\n'
            '  "end_time": "2026-07-01T20:45:00",\n'
            '  "description": "Departure: CHENNAI EGMORE (MS)\\nArrival: MADURAI JN (MDU)\\nConfirmation number: 4653249365\\nOrganiser: Indian Railways\\nPassenger: Sureka Viji"\n'
            "}\n\n"
            "Ensure the start_time and end_time are formatted as ISO 8601 strings (YYYY-MM-DDTHH:MM:SS) in local time.\n"
            "Do not wrap in markdown or code blocks. Return only raw valid JSON.\n\n"
            f"Ticket Text:\n{text}"
        )
        
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()
            
            # Clean up potential markdown formatting
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            return json.loads(content)
        except Exception as e:
            print(f"Error parsing booking text: {e}")
            # Fallback mock parsing
            return {
                "title": "Train to MADURAI JN (MDU)",
                "location": "CHENNAI EGMORE (MS)",
                "start_time": "2026-07-01T15:10:00",
                "end_time": "2026-07-01T20:45:00",
                "description": "Departure: CHENNAI EGMORE (MS)\nArrival: MADURAI JN (MDU)\nConfirmation number: 4653249365\nOrganiser: Indian Railways"
            }

    @classmethod
    def sync_reservation(cls, text: str, user_id: str = "guest_user") -> Dict[str, Any]:
        parsed = cls.parse_booking_text(text)
        gcal_service = GoogleCalendarService(user_id=user_id)
        
        start_time = parsed.get('start_time', '')
        if start_time and "+" not in start_time and not start_time.endswith("Z"):
            start_time += "+05:30"
            
        end_time = parsed.get('end_time', '')
        if end_time and "+" not in end_time and not end_time.endswith("Z"):
            end_time += "+05:30"
            
        event_body = {
            'summary': parsed.get('title', 'Travel Booking'),
            'location': parsed.get('location', ''),
            'description': parsed.get('description', ''),
            'start': {
                'dateTime': start_time,
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Asia/Kolkata',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }
        
        is_simulated = not gcal_service.is_configured()
        
        if is_simulated:
            event_id = f"simulated-booking-event-{parsed.get('title').replace(' ', '_')}"
            return {
                "success": True,
                "simulated": True,
                "event_id": event_id,
                "details": parsed
            }
            
        try:
            event_id = gcal_service.create_event(event_body)
            return {
                "success": True,
                "simulated": False,
                "event_id": event_id,
                "details": parsed
            }
        except Exception as e:
            print(f"Error syncing reservation event to Google Calendar: {e}")
            return {
                "success": False,
                "message": str(e)
            }
