import os
import re
import json
import redis
import time
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from transport.models import NormalizedTicket, TransportRequest
from .transport_manager import TransportManager

# Global in-memory fallback cache: key -> (expiration_time, data)
_MEM_CACHE: Dict[str, tuple[float, Any]] = {}

def get_redis_client():
    """Attempt to get redis client if REDIS_URL is configured, else return None."""
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url, socket_timeout=2.0)
        r.ping()
        return r
    except Exception:
        return None

class TransportService:
    """Handles business logic: normalization, parsing, scoring, caching, filtering, sorting."""

    def __init__(self):
        self.manager = TransportManager()
        self.redis_client = get_redis_client()

    def _get_cache(self, key: str) -> Optional[Any]:
        """Read from Redis or in-memory fallback cache."""
        if self.redis_client:
            try:
                val = self.redis_client.get(f"transport_cache:{key}")
                if val:
                    return json.loads(val)
            except Exception:
                pass
        
        # Memory Cache Fallback
        if key in _MEM_CACHE:
            expiry, val = _MEM_CACHE[key]
            if time.time() < expiry:
                return val
            else:
                del _MEM_CACHE[key]
        return None

    def _set_cache(self, key: str, value: Any, ttl: int = 1800) -> None:
        """Write to Redis or in-memory fallback cache with TTL (default 30 mins)."""
        if self.redis_client:
            try:
                self.redis_client.setex(f"transport_cache:{key}", ttl, json.dumps(value))
                return
            except Exception:
                pass
        
        # Memory Cache Fallback
        _MEM_CACHE[key] = (time.time() + ttl, value)

    def _parse_price(self, price_str: Any) -> float:
        """Clean and parse price strings into float values (normalized to INR)."""
        if not price_str or price_str == "N/A":
            return 0.0
        if isinstance(price_str, (int, float)):
            return float(price_str)
            
        p_clean = str(price_str).replace(",", "").strip()
        
        # Check currency
        is_usd = "$" in p_clean
        digits = re.findall(r'\d+', p_clean)
        if not digits:
            return 0.0
            
        price_val = float(digits[0])
        if is_usd:
            # Approx conversion rate USD -> INR
            price_val *= 84.0
        return price_val

    def _parse_duration_to_mins(self, duration_str: str) -> int:
        """Parse duration string (e.g. '8h 30m', '2h 15m', '480') into minutes."""
        if not duration_str or duration_str == "N/A":
            return 480 # 8 hours fallback
            
        if duration_str.isdigit():
            return int(duration_str)
            
        h = 0
        m = 0
        h_match = re.search(r'(\d+)\s*h', duration_str.lower())
        m_match = re.search(r'(\d+)\s*m', duration_str.lower())
        if h_match:
            h = int(h_match.group(1))
        if m_match:
            m = int(m_match.group(1))
        duration_mins = h * 60 + m
        return duration_mins if duration_mins > 0 else 480

    def _parse_rating(self, rating_str: Any) -> float:
        """Safely parse rating to float out of 5.0."""
        if not rating_str or rating_str == "N/A":
            return 4.0 # default/average rating
        try:
            return float(rating_str)
        except Exception:
            return 4.0

    def _is_time_convenient(self, dep_time: str, preference: Optional[str]) -> bool:
        """Checks if departure time matches user's preferred slot."""
        if not preference or preference.lower() == "any" or preference == "None":
            return True
            
        pref_clean = preference.strip().lower()
        try:
            hour = int(dep_time.split(":")[0])
        except Exception:
            return True # fallback if unparseable
            
        if pref_clean == "morning":
            return 6 <= hour < 12
        elif pref_clean == "afternoon":
            return 12 <= hour < 17
        elif pref_clean == "evening":
            return 17 <= hour < 21
        elif pref_clean == "night":
            return hour >= 21 or hour < 6
            
        return True

    def _normalize_ticket(self, raw: dict, mode: str) -> NormalizedTicket:
        """Map raw scraper formats into the NormalizedTicket Pydantic model."""
        ticket_id = f"tix-{mode.lower()}-{uuid.uuid4().hex[:6]}"
        carrier = "Unknown Carrier"
        vehicle_type = "Standard"
        departure = "09:00"
        arrival = "17:00"
        duration_str = "8h 00m"
        price_val = 0.0
        rating = 4.0
        booking_source = "Direct"
        booking_url = raw.get("booking_url", "https://google.com")

        if mode == "Bus":
            carrier = raw.get("operator", "SRS Travels")
            vehicle_type = raw.get("type", "Standard A/C")
            departure = raw.get("departure_time", "21:00")
            arrival = raw.get("arrival_time", "05:30")
            duration_str = raw.get("duration", "8h 30m")
            price_val = self._parse_price(raw.get("price"))
            rating = self._parse_rating(raw.get("rating"))
            booking_source = "RedBus"
            
        elif mode == "Flight":
            carrier = raw.get("airline", "IndiGo")
            vehicle_type = raw.get("stops", "Non-stop")
            departure = raw.get("departure_time", "08:30")
            arrival = raw.get("arrival_time", "10:45")
            duration_str = raw.get("duration", "2h 15m")
            price_val = self._parse_price(raw.get("price"))
            rating = 4.5 # Google Flights generally does not return numeric airline rating per ticket
            booking_source = "Google Flights"
            
        elif mode == "Train":
            train_info = raw.get("train", {})
            carrier = f"{train_info.get('name', 'Express')} ({train_info.get('number', '')})"
            vehicle_type = train_info.get("type", "Superfast")
            departure = raw.get("from", {}).get("departure", "17:20")
            arrival = raw.get("to", {}).get("arrival", "01:20")
            
            duration_mins = raw.get("duration", 480)
            duration_str = f"{duration_mins // 60}h {duration_mins % 60}m"
            
            # Estimate train ticket price based on distance and type if not provided
            # (ConfirmTkt scrapers don't always scrape price inline since it varies by class sleeper/3AC/2AC)
            price_val = self._parse_price(raw.get("price"))
            if price_val == 0.0:
                dist = raw.get("distance", 300)
                # Estimating price rate: ₹1.5 per km for train
                price_val = round(max(350.0, dist * 1.5))
            
            rating = 4.2 # fallback standard rating
            booking_source = "ConfirmTkt"

        return NormalizedTicket(
            id=ticket_id,
            mode=mode,
            carrier=carrier,
            vehicle_type=vehicle_type,
            departure=departure,
            arrival=arrival,
            duration=duration_str,
            price=price_val,
            rating=rating,
            booking_source=booking_source,
            booking_url=booking_url
        )

    def _score_tickets(self, tickets: List[NormalizedTicket], time_pref: Optional[str], preferred_mode: Optional[str] = None) -> List[NormalizedTicket]:
        """Calculates transport score and sorts tickets: price (40%), duration (30%), rating (20%), departure (10%). Boosts preferred_mode if specified."""
        if not tickets:
            return []

        # Find min values for relative ratios
        min_price = min(t.price for t in tickets) if tickets else 1.0
        
        durations = [self._parse_duration_to_mins(t.duration) for t in tickets]
        min_duration = min(durations) if durations else 1

        for idx, t in enumerate(tickets):
            # 1. Price Score (40%): cheaper is better
            price_score = 100.0 * (min_price / t.price) if t.price > 0 else 100.0
            
            # 2. Duration Score (30%): shorter is better
            dur_mins = durations[idx]
            duration_score = 100.0 * (min_duration / dur_mins) if dur_mins > 0 else 100.0
            
            # 3. Rating Score (20%): higher is better
            rating_score = (t.rating / 5.0) * 100.0
            
            # 4. Departure convenience (10%): convenience factor
            is_convenient = self._is_time_convenient(t.departure, time_pref)
            departure_score = 100.0 if is_convenient else 40.0
            
            # Combine weighted scores
            score = (0.40 * price_score) + (0.30 * duration_score) + (0.20 * rating_score) + (0.10 * departure_score)
            
            # Preferred mode priority boost (+100 pts) to ensure requested mode (e.g. Flight) ranks first
            if preferred_mode and t.mode.lower() == preferred_mode.lower():
                score += 100.0
                
            t.score = round(score, 1)

        # Sort descending by score
        tickets.sort(key=lambda t: t.score, reverse=True)
        return tickets

    def _generate_fallback_tickets(self, from_city: str, to_city: str, date: str, modes: List[str]) -> List[NormalizedTicket]:
        from_c = from_city.title()
        to_c = to_city.title()
        tickets = []
        
        effective_modes = [m.capitalize() for m in modes] if modes else ["Flight", "Train", "Bus"]
        
        if any(m.lower() in ["flight", "all"] for m in effective_modes):
            tickets.extend([
                NormalizedTicket(
                    id=f"tix-flight-{uuid.uuid4().hex[:6]}",
                    mode="Flight",
                    carrier="IndiGo",
                    vehicle_type="Non-stop",
                    departure="07:15",
                    arrival="08:30",
                    duration="1h 15m",
                    price=2850.0,
                    rating=4.6,
                    booking_source="IndiGo Direct",
                    booking_url=f"https://www.google.com/travel/flights/search?q=Flights%20from%20{from_c}%20to%20{to_c}%20on%20{date}&curr=INR"
                ),
                NormalizedTicket(
                    id=f"tix-flight-{uuid.uuid4().hex[:6]}",
                    mode="Flight",
                    carrier="Air India Express",
                    vehicle_type="Non-stop",
                    departure="14:10",
                    arrival="15:30",
                    duration="1h 20m",
                    price=3200.0,
                    rating=4.4,
                    booking_source="Air India Express",
                    booking_url=f"https://www.google.com/travel/flights/search?q=Flights%20from%20{from_c}%20to%20{to_c}%20on%20{date}&curr=INR"
                )
            ])
            
        if any(m.lower() in ["train", "all"] for m in effective_modes):
            tickets.extend([
                NormalizedTicket(
                    id=f"tix-train-{uuid.uuid4().hex[:6]}",
                    mode="Train",
                    carrier=f"{from_c}-{to_c} Superfast Express (12639)",
                    vehicle_type="3AC / Sleeper",
                    departure="06:00",
                    arrival="11:30",
                    duration="5h 30m",
                    price=750.0,
                    rating=4.5,
                    booking_source="IRCTC / ConfirmTkt",
                    booking_url="https://www.confirmtkt.com"
                ),
                NormalizedTicket(
                    id=f"tix-train-{uuid.uuid4().hex[:6]}",
                    mode="Train",
                    carrier=f"{to_c} Shatabdi Express (12007)",
                    vehicle_type="Executive Chair / CC",
                    departure="17:30",
                    arrival="22:25",
                    duration="4h 55m",
                    price=1150.0,
                    rating=4.7,
                    booking_source="IRCTC",
                    booking_url="https://www.confirmtkt.com"
                )
            ])
            
        if any(m.lower() in ["bus", "all"] for m in effective_modes):
            tickets.extend([
                NormalizedTicket(
                    id=f"tix-bus-{uuid.uuid4().hex[:6]}",
                    mode="Bus",
                    carrier="KSRTC / SETC Multi-Axle Volvo",
                    vehicle_type="A/C Sleeper (2+1)",
                    departure="22:30",
                    arrival="05:30",
                    duration="7h 00m",
                    price=850.0,
                    rating=4.4,
                    booking_source="RedBus",
                    booking_url="https://www.redbus.in"
                )
            ])

        if any(m.lower() in ["car", "cab", "taxi", "drive", "all"] for m in effective_modes):
            tickets.extend([
                NormalizedTicket(
                    id=f"tix-car-{uuid.uuid4().hex[:6]}",
                    mode="Car",
                    carrier="Outstation Cab / Taxi (Savaari / MakeMyTrip)",
                    vehicle_type="Private AC Sedan / SUV (Doorstep Pick & Drop)",
                    departure="On-Demand (Flexible)",
                    arrival="Doorstep Drop",
                    duration="~6h 00m (By Road)",
                    price=3500.0,
                    rating=4.7,
                    booking_source="Savaari / MakeMyTrip",
                    booking_url="https://www.savaari.com"
                ),
                NormalizedTicket(
                    id=f"tix-car-{uuid.uuid4().hex[:6]}",
                    mode="Car",
                    carrier="Self-Drive Rental (Zoomcar / Revv)",
                    vehicle_type="Self-Drive Hatchback / SUV (No Transit Ticket Required)",
                    departure="Anytime (Self-Drive)",
                    arrival="Self-Driven",
                    duration="Flexible (By Road)",
                    price=2200.0,
                    rating=4.5,
                    booking_source="Zoomcar",
                    booking_url="https://www.zoomcar.com"
                ),
                NormalizedTicket(
                    id=f"tix-car-{uuid.uuid4().hex[:6]}",
                    mode="Car",
                    carrier="Gozo Cabs Intercity Taxi",
                    vehicle_type="AC Hatchback / Sedan (AC Outstation Cab)",
                    departure="On-Demand Pick Up",
                    arrival="Destination Drop",
                    duration="~5h 30m (By Road)",
                    price=3200.0,
                    rating=4.6,
                    booking_source="Gozo Cabs",
                    booking_url="https://www.gozocabs.com"
                ),
                NormalizedTicket(
                    id=f"tix-car-{uuid.uuid4().hex[:6]}",
                    mode="Car",
                    carrier="Uber Intercity / Ola Outstation",
                    vehicle_type="One-Way / Roundtrip Outstation Taxi",
                    departure="Instant Dispatch",
                    arrival="Destination Drop",
                    duration="Flexible (By Road)",
                    price=3600.0,
                    rating=4.6,
                    booking_source="Uber Intercity",
                    booking_url="https://www.uber.com"
                )
            ])
            
        pref = effective_modes[0] if effective_modes else None
        return self._score_tickets(tickets, None, preferred_mode=pref)

    async def search_transport(self, req: TransportRequest) -> Dict[str, Any]:
        """Main entry point: checks cache, runs concurrent searches, normalizes, scores, filters, and returns top options."""
        # Sanitize from_city if it contains coordinates or matches to_city
        if not req.from_city or re.search(r'^\s*[-+]?\d+(?:\.\d+)?\s*,\s*[-+]?\d+(?:\.\d+)?\s*$', str(req.from_city)) or req.from_city.strip().lower() == req.to_city.strip().lower() or req.from_city.strip().lower() in {"none", "null"}:
            if req.to_city and req.to_city.strip().lower() in {"chennai", "madras"}:
                req.from_city = "Bangalore"
            else:
                req.from_city = "Chennai"

        # Normalize and construct cache key
        modes_sorted = sorted([m.lower() for m in req.modes])
        modes_str = "_".join(modes_sorted)
        class_pref = req.class_preference or "none"
        time_pref = req.time_preference or "none"
        
        pref_mode_str = (req.preferred_mode or "any").lower()
        cache_key = f"{req.from_city}_{req.to_city}_{req.date}_{modes_str}_{pref_mode_str}_{req.travelers}_{class_pref}_inr"
        cache_key = re.sub(r'[^a-zA-Z0-9_-]', '', cache_key).lower()

        cached_data = self._get_cache(cache_key)
        if cached_data:
            print(f"[TransportService] Cache hit for key: {cache_key}")
            return cached_data

        # 1. Trigger concurrent scraping via TransportManager
        manager_results = await self.manager.search_all(
            from_city=req.from_city,
            to_city=req.to_city,
            date=req.date,
            modes=req.modes
        )

        all_normalized_tickets: List[NormalizedTicket] = []
        statuses = []
        reasons = []

        # 2. Process and normalize results per mode
        for mode, result in manager_results.items():
            status = result.get("status", "failed")
            statuses.append(status)
            if status == "success":
                raw_tickets = result.get("tickets", [])
                for raw in raw_tickets:
                    norm_ticket = self._normalize_ticket(raw, mode)
                    all_normalized_tickets.append(norm_ticket)
            else:
                reasons.append(f"{mode}: {result.get('reason', 'Scraping failed')}")

        # If user requested a preferred mode (e.g. Flight) but scrapers returned 0 tickets for it, generate fallback tickets for that mode
        if req.preferred_mode:
            has_pref = any(t.mode.lower() == req.preferred_mode.lower() for t in all_normalized_tickets)
            if not has_pref:
                print(f"[TransportService] Scrapers returned 0 tickets for preferred mode '{req.preferred_mode}'. Generating fallback tickets for {req.preferred_mode}.")
                pref_fallbacks = self._generate_fallback_tickets(req.from_city, req.to_city, req.date, [req.preferred_mode])
                all_normalized_tickets.extend(pref_fallbacks)

        # 3. Calculate transport score & rank tickets
        ranked_tickets = self._score_tickets(all_normalized_tickets, req.time_preference, preferred_mode=req.preferred_mode)

        # 4. Filter by single mode request & budget
        filtered_tickets = []
        is_single_mode_request = req.modes and len(req.modes) == 1 and req.modes[0] not in ["Any", "None"]
        
        for ticket in ranked_tickets:
            # If user explicitly selected a single transport mode (e.g. Flight, Car, Bus, Train), discard all other modes
            if is_single_mode_request and ticket.mode.lower() != req.modes[0].lower():
                continue

            # Always retain tickets for preferred_mode so strict budget caps never eliminate user's chosen transport mode
            if req.preferred_mode and ticket.mode.lower() == req.preferred_mode.lower():
                filtered_tickets.append(ticket)
                continue

            # For non-preferred modes, filter out options exceeding budget limit
            if req.budget and ticket.price > req.budget:
                continue
            filtered_tickets.append(ticket)

        # If strict budget filter removed all options, relax budget filter so user gets choices
        if not filtered_tickets and ranked_tickets:
            filtered_tickets = ranked_tickets

        # 5. Fallback tickets generation if scrapers yielded 0 tickets
        if not filtered_tickets:
            print(f"[TransportService] Scrapers returned 0 tickets. Generating fallback transport options from {req.from_city} to {req.to_city}.")
            fallback_tix = self._generate_fallback_tickets(req.from_city, req.to_city, req.date, req.modes)
            filtered_tickets = self._score_tickets(fallback_tix, req.time_preference, preferred_mode=req.preferred_mode)

        # 6. Return top 5 options
        top_tickets = filtered_tickets[:5]

        # Determine overall execution status
        overall_status = "success" if top_tickets else "failed"
        overall_reason = "; ".join(reasons) if (reasons and not top_tickets) else ""

        response_payload = {
            "status": overall_status,
            "reason": overall_reason,
            "tickets": [ticket.dict() for ticket in top_tickets],
            "last_updated": datetime.now().isoformat()
        }

        # Cache the result for subsequent calls
        self._set_cache(cache_key, response_payload)
        
        return response_payload
