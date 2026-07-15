import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any

class NotificationSchedulerService:
    @staticmethod
    def schedule(notifications: List[Dict[str, Any]], itinerary_items: List[Dict[str, Any]], travel_date_str: str = None) -> List[Dict[str, Any]]:
        """
        De-duplicates, sets status transitions, parses relative event times to ISO timestamps,
        assigns default priorities, and sorts notifications chronologically.
        """
        
        # 1. Resolve Trip Start Date
        base_date = datetime.now() + timedelta(days=1)
        if travel_date_str:
            try:
                base_date = datetime.strptime(travel_date_str.strip(), "%Y-%m-%d")
            except:
                pass

        # 2. Map itinerary items to helper lookup dictionary for quick trigger time math
        itinerary_times = {}
        for idx, item in enumerate(itinerary_items):
            day = int(item.get("day", 1))
            start_time = item.get("start_time", "09:00")
            activity = item.get("activity", "")
            
            # Resolve time (HH:MM)
            hour, minute = 9, 0
            if ":" in start_time:
                try:
                    parts = start_time.split(":")
                    hour = int(parts[0])
                    minute = int(parts[1][:2])
                except:
                    pass
            
            # Compute exact event time
            event_datetime = base_date + timedelta(days=(day - 1))
            event_datetime = event_datetime.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Save mapping
            key = f"day{day}_{start_time}_{activity.lower()[:15]}"
            itinerary_times[key] = event_datetime
            
            # Fallback mappings
            itinerary_times[f"day{day}_{start_time}"] = event_datetime
            itinerary_times[activity.lower()] = event_datetime

        # 3. Process, clean, and resolve notifications
        seen_keys = set()
        scheduled_list = []
        
        # Priority mapping fallback weights
        priority_weights = {
            "critical": 1,
            "high": 2,
            "medium": 3,
            "low": 4
        }
        
        trigger_weights = {
            "immediate": 0,
            "trip_created": 1,
            "calendar_saved": 2,
            "1_day_before": 3,
            "trip_started": 4,
            "2_hours_before": 5,
            "30_minutes_before": 6,
            "arrival": 7,
            "meal_time": 8,
            "departure": 9,
            "evening": 10
        }

        for n in notifications:
            # Clean duplicate messages
            title = n.get("title", "Update").strip()
            voice = n.get("voice", "").strip()
            if not voice:
                continue
                
            dedup_key = f"{title.lower()}_{voice.lower()[:30]}"
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)
            
            # Extract standard fields
            n_id = n.get("id") or f"notif_{uuid.uuid4().hex[:8]}"
            n_type = n.get("type", "general")
            n_source = n.get("source", "itinerary")
            n_priority = n.get("priority", "medium").lower()
            if n_priority not in priority_weights:
                n_priority = "medium"
                
            n_trigger = n.get("trigger", "immediate").lower()
            if n_trigger not in trigger_weights:
                n_trigger = "immediate"
                
            raw_event_time = n.get("event_time")
            n_text = n.get("text", "")
            n_play_voice = n.get("play_voice", True)
            n_spoken = n.get("spoken", False)
            n_status = n.get("status", "pending")
            n_action = n.get("action")
            
            # 4. Compute ISO trigger event time
            event_iso = None
            if n_trigger == "trip_created" or n_trigger == "calendar_saved" or n_trigger == "immediate":
                event_iso = datetime.now().isoformat()
            elif n_trigger == "1_day_before":
                event_iso = (base_date - timedelta(days=1)).replace(hour=9, minute=0).isoformat()
            elif n_trigger == "trip_started":
                event_iso = base_date.replace(hour=8, minute=0).isoformat()
            elif n_trigger == "evening":
                event_iso = base_date.replace(hour=19, minute=0).isoformat()
            else:
                # Resolve using itinerary maps
                event_dt = None
                if raw_event_time:
                    # Check in itinerary times
                    match_key = str(raw_event_time).lower()
                    event_dt = itinerary_times.get(match_key)
                    if not event_dt:
                        # Try parsing day prefix
                        for key, val in itinerary_times.items():
                            if key in match_key or match_key in key:
                                event_dt = val
                                break
                
                # If no matching event, fallback to day 1 morning/afternoon times
                if not event_dt:
                    if n_trigger == "meal_time":
                        event_dt = base_date.replace(hour=13, minute=0)
                    else:
                        event_dt = base_date.replace(hour=9, minute=0)
                        
                event_iso = event_dt.isoformat()
            
            # If the trigger is in the past, transition status to expired
            if event_iso:
                try:
                    event_dt = datetime.fromisoformat(event_iso)
                    if event_dt < datetime.now() - timedelta(hours=1):
                        n_status = "expired"
                except:
                    pass

            scheduled_list.append({
                "id": n_id,
                "type": n_type,
                "source": n_source,
                "priority": n_priority,
                "trigger": n_trigger,
                "event_time": event_iso,
                "title": title,
                "text": n_text,
                "voice": voice,
                "play_voice": n_play_voice,
                "spoken": n_spoken,
                "status": n_status,
                "action": n_action
            })

        # 5. Sort notifications chronologically by trigger event_time or category weights
        def sort_key(notif):
            evt_time = notif.get("event_time")
            if evt_time:
                try:
                    return datetime.fromisoformat(evt_time)
                except:
                    pass
            # Trigger weights fallback
            trig = notif.get("trigger", "immediate")
            return datetime.max - timedelta(days=(10 - trigger_weights.get(trig, 99)))

        scheduled_list.sort(key=sort_key)
        return scheduled_list
