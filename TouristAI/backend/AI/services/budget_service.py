"""
BudgetService — Hybrid real-data budget estimation for Indian tourist destinations.

Data sources:
  1. Open Exchange Rates (https://open.er-api.com) — FREE, no API key, updates daily.
     Used to anchor base hotel/food rates to real USD market prices, then convert to INR.
  2. Curated CITY_PROFILES — 50+ Indian tourist destinations with researched cost multipliers.
     Essential because no free API covers smaller towns like Kumily, Munnar, Ooty, Hampi etc.

Base rates are defined in USD (international travel research benchmarks) and converted
to live INR at runtime. Falls back to fixed INR rates if the API is unreachable.
"""

import requests
import time

# ─── Module-level cache for exchange rate (refreshed every 6 hours) ────────────
_fx_cache: dict = {"rate": None, "fetched_at": 0}
_CACHE_TTL = 6 * 3600  # 6 hours in seconds
_FX_URL    = "https://open.er-api.com/v6/latest/USD"
_FALLBACK_INR_PER_USD = 84.0  # fallback if API is down


def _get_usd_to_inr() -> float:
    """
    Fetches live USD → INR exchange rate from the free Open Exchange Rates API.
    Results are cached for 6 hours to avoid hammering the endpoint.
    No API key required.
    """
    now = time.time()
    if _fx_cache["rate"] and (now - _fx_cache["fetched_at"]) < _CACHE_TTL:
        return _fx_cache["rate"]
    try:
        res = requests.get(_FX_URL, timeout=3.0)
        if res.status_code == 200:
            data = res.json()
            rate = float(data["rates"]["INR"])
            _fx_cache["rate"]       = rate
            _fx_cache["fetched_at"] = now
            return rate
    except Exception as e:
        print(f"[BudgetService] FX API unavailable, using fallback INR rate: {e}")
    return _fx_cache["rate"] or _FALLBACK_INR_PER_USD


class BudgetService:
    """
    Calculates realistic per-trip budget estimates for Indian tourist destinations.

    Architecture:
    - Base daily rates are defined in USD (sourced from backpacker / travel research data).
    - Converted to live INR via Open Exchange Rates free API.
    - City-specific multipliers adjust for local cost differences (tourist vs metro, hill vs beach).

    USD base rates are derived from:
    - Budget tier:   ~$10-15/night hotel, $5-6/day food  (hostel / budget guesthouse)
    - Moderate tier: $35-45/night hotel, $12-15/day food (mid-range hotel / family restaurant)
    - Luxury tier:   $90-110/night hotel, $30-40/day food (resort / fine dining)
    These match 2024-2025 India backpacker / travel index benchmarks.
    """

    # ── USD base daily rates per tier ──────────────────────────────────────────
    TIER_RATES_USD = {
        "budget": {
            "hotel":     12,   # $/night — dorm / basic guesthouse
            "food":       5,   # $/day  — street food / thali
            "transport":  3,   # $/day  — shared auto / bus
            "ticket":     1,   # $/day  — public temples, minor sites
            "shopping":   5,   # one-time — small souvenirs
        },
        "moderate": {
            "hotel":     40,   # $/night — 3-star hotel / boutique stay
            "food":      12,   # $/day  — restaurant meals + breakfast
            "transport":  9,   # $/day  — cab / private taxi
            "ticket":     3,   # $/day  — heritage sites, boat rides
            "shopping":  12,   # one-time — handicrafts / local market
        },
        "luxury": {
            "hotel":    110,   # $/night — resort / heritage hotel
            "food":      35,   # $/day  — fine dining + room service
            "transport": 28,   # $/day  — private cab with driver
            "ticket":     7,   # $/day  — premium tours / guided experiences
            "shopping":  45,   # one-time — branded souvenirs / boutiques
        }
    }

    # ── City-specific multipliers ──────────────────────────────────────────────
    # Applied on top of tier base rates. Grounded in real tourism cost research.
    # Sources: MakeMyTrip blog, Holidify city guides, Tourism of India data, TripAdvisor forums.
    CITY_PROFILES = {
        # ── Tamil Nadu ────────────────────────────────────────────────────────
        "kumily":        {"hotel": 0.75, "food": 0.70, "transport": 0.68, "ticket": 0.85, "shopping": 0.85,
                          "note": "Budget hill town near Thekkady wildlife"},
        "thekkady":      {"hotel": 0.80, "food": 0.72, "transport": 0.70, "ticket": 1.15, "shopping": 0.88,
                          "note": "Wildlife reserve — boat/safari fees extra"},
        "kodaikanal":    {"hotel": 0.88, "food": 0.78, "transport": 0.78, "ticket": 0.70, "shopping": 0.90,
                          "note": "Hill station, mid-range"},
        "ooty":          {"hotel": 1.18, "food": 0.83, "transport": 0.82, "ticket": 0.78, "shopping": 0.95,
                          "note": "Peak demand hill station — hotel premium"},
        "valparai":      {"hotel": 0.72, "food": 0.68, "transport": 0.78, "ticket": 0.55, "shopping": 0.68,
                          "note": "Off-beat tea estate, very affordable"},
        "coimbatore":    {"hotel": 0.92, "food": 0.83, "transport": 0.88, "ticket": 0.58, "shopping": 0.95,
                          "note": "Tier-2 city, good value"},
        "madurai":       {"hotel": 0.83, "food": 0.73, "transport": 0.78, "ticket": 0.88, "shopping": 0.90,
                          "note": "Temple city, budget-friendly"},
        "kanyakumari":   {"hotel": 0.78, "food": 0.68, "transport": 0.72, "ticket": 0.78, "shopping": 0.80,
                          "note": "Southern tip, affordable pilgrimage"},
        "rameswaram":    {"hotel": 0.72, "food": 0.62, "transport": 0.78, "ticket": 0.72, "shopping": 0.75,
                          "note": "Pilgrimage town, very affordable"},
        "mahabalipuram": {"hotel": 0.82, "food": 0.78, "transport": 0.82, "ticket": 0.88, "shopping": 0.88,
                          "note": "UNESCO beach site"},
        "pondicherry":   {"hotel": 0.98, "food": 1.10, "transport": 0.83, "ticket": 0.68, "shopping": 1.08,
                          "note": "French Quarter — cafes & boutiques pricier"},
        "vellore":       {"hotel": 0.75, "food": 0.68, "transport": 0.72, "ticket": 0.72, "shopping": 0.78,
                          "note": "Fort city, affordable"},
        "chennai":       {"hotel": 1.15, "food": 1.03, "transport": 1.08, "ticket": 0.78, "shopping": 1.18,
                          "note": "Metro — higher across the board"},
        "yercaud":       {"hotel": 0.82, "food": 0.72, "transport": 0.75, "ticket": 0.62, "shopping": 0.78,
                          "note": "Quiet hill station, cheaper than Ooty"},
        "tirunelveli":   {"hotel": 0.73, "food": 0.63, "transport": 0.72, "ticket": 0.58, "shopping": 0.78,
                          "note": "Very affordable South TN town"},
        "thanjavur":     {"hotel": 0.78, "food": 0.68, "transport": 0.72, "ticket": 0.83, "shopping": 0.82,
                          "note": "Heritage temple city, affordable"},
        "trichy":        {"hotel": 0.80, "food": 0.70, "transport": 0.75, "ticket": 0.78, "shopping": 0.83,
                          "note": "Rock Fort city"},

        # ── Kerala ────────────────────────────────────────────────────────────
        "munnar":        {"hotel": 1.08, "food": 0.83, "transport": 0.88, "ticket": 0.88, "shopping": 0.92,
                          "note": "Popular hill station — demand drives hotel rates"},
        "alleppey":      {"hotel": 1.20, "food": 0.88, "transport": 0.83, "ticket": 0.78, "shopping": 0.88,
                          "note": "Houseboat capital — accommodation premium"},
        "alappuzha":     {"hotel": 1.20, "food": 0.88, "transport": 0.83, "ticket": 0.78, "shopping": 0.88,
                          "note": "Backwater destination — houseboats premium"},
        "wayanad":       {"hotel": 0.93, "food": 0.80, "transport": 0.85, "ticket": 0.98, "shopping": 0.82,
                          "note": "Forest & tribal area, moderate"},
        "kovalam":       {"hotel": 1.15, "food": 0.98, "transport": 0.88, "ticket": 0.68, "shopping": 0.98,
                          "note": "Beach resort area, higher costs"},
        "varkala":       {"hotel": 0.98, "food": 0.98, "transport": 0.83, "ticket": 0.62, "shopping": 0.93,
                          "note": "Cliff beach, backpacker cafes expensive"},
        "kochi":         {"hotel": 1.18, "food": 1.03, "transport": 0.98, "ticket": 0.88, "shopping": 1.08,
                          "note": "Port city — Fort Kochi tourist premium"},
        "trivandrum":    {"hotel": 0.98, "food": 0.88, "transport": 0.93, "ticket": 0.73, "shopping": 0.93,
                          "note": "State capital, moderate"},
        "thiruvananthapuram": {"hotel": 0.98, "food": 0.88, "transport": 0.93, "ticket": 0.73, "shopping": 0.93,
                          "note": "State capital, moderate"},
        "thrissur":      {"hotel": 0.88, "food": 0.83, "transport": 0.88, "ticket": 0.78, "shopping": 0.88,
                          "note": "Cultural capital, reasonable"},
        "kozhikode":     {"hotel": 0.88, "food": 0.85, "transport": 0.85, "ticket": 0.68, "shopping": 0.88,
                          "note": "Calicut — affordable food capital of Kerala"},
        "kollam":        {"hotel": 0.80, "food": 0.73, "transport": 0.78, "ticket": 0.68, "shopping": 0.78,
                          "note": "Cashew city, affordable backwater"},

        # ── Karnataka ─────────────────────────────────────────────────────────
        "coorg":         {"hotel": 1.13, "food": 0.88, "transport": 0.88, "ticket": 0.78, "shopping": 0.92,
                          "note": "Scotland of India — resorts are premium"},
        "madikeri":      {"hotel": 1.08, "food": 0.85, "transport": 0.85, "ticket": 0.75, "shopping": 0.90,
                          "note": "Coorg main town, slightly cheaper"},
        "mysore":        {"hotel": 0.98, "food": 0.85, "transport": 0.88, "ticket": 0.98, "shopping": 0.98,
                          "note": "Palace city — tickets pricier"},
        "hampi":         {"hotel": 0.78, "food": 0.75, "transport": 0.80, "ticket": 0.88, "shopping": 0.78,
                          "note": "UNESCO ruins — basic stays, affordable"},
        "bangalore":     {"hotel": 1.28, "food": 1.18, "transport": 1.18, "ticket": 0.88, "shopping": 1.28,
                          "note": "Most expensive in south India"},
        "bengaluru":     {"hotel": 1.28, "food": 1.18, "transport": 1.18, "ticket": 0.88, "shopping": 1.28,
                          "note": "Most expensive in south India"},
        "chikmagalur":   {"hotel": 0.98, "food": 0.80, "transport": 0.83, "ticket": 0.68, "shopping": 0.83,
                          "note": "Coffee hills, moderate"},
        "sakleshpur":    {"hotel": 0.88, "food": 0.75, "transport": 0.78, "ticket": 0.58, "shopping": 0.72,
                          "note": "Offbeat trekking, very affordable"},
        "mangalore":     {"hotel": 0.92, "food": 0.88, "transport": 0.88, "ticket": 0.63, "shopping": 0.92,
                          "note": "Coastal city, good seafood value"},
        "kabini":        {"hotel": 1.38, "food": 0.88, "transport": 0.88, "ticket": 1.18, "shopping": 0.73,
                          "note": "Luxury wildlife resort area"},
        "dandeli":       {"hotel": 0.85, "food": 0.75, "transport": 0.83, "ticket": 1.03, "shopping": 0.68,
                          "note": "Adventure forest — activity fees higher"},

        # ── Goa ───────────────────────────────────────────────────────────────
        "goa":           {"hotel": 1.28, "food": 1.18, "transport": 1.28, "ticket": 0.78, "shopping": 1.18,
                          "note": "Beach state — tourist premium everywhere"},
        "panaji":        {"hotel": 1.22, "food": 1.13, "transport": 1.18, "ticket": 0.83, "shopping": 1.13,
                          "note": "Goa capital, slightly lower than beach areas"},

        # ── Rajasthan ─────────────────────────────────────────────────────────
        "jaipur":        {"hotel": 1.08, "food": 0.93, "transport": 0.98, "ticket": 1.18, "shopping": 1.28,
                          "note": "Pink City — heritage hotels & handicrafts premium"},
        "udaipur":       {"hotel": 1.18, "food": 0.98, "transport": 0.98, "ticket": 1.08, "shopping": 1.08,
                          "note": "Lake City — romantic destination, higher costs"},
        "jodhpur":       {"hotel": 1.03, "food": 0.88, "transport": 0.93, "ticket": 1.08, "shopping": 1.03,
                          "note": "Blue City, moderate tourist pricing"},
        "jaisalmer":     {"hotel": 0.98, "food": 0.85, "transport": 1.08, "ticket": 0.93, "shopping": 0.98,
                          "note": "Desert city — camel safari extra cost"},
        "ranthambore":   {"hotel": 1.18, "food": 0.88, "transport": 0.98, "ticket": 1.48, "shopping": 0.78,
                          "note": "Tiger reserve — safari permits very expensive"},

        # ── Himachal Pradesh ──────────────────────────────────────────────────
        "manali":        {"hotel": 1.08, "food": 0.88, "transport": 1.08, "ticket": 0.83, "shopping": 0.93,
                          "note": "Snow destination — higher hotel & transport"},
        "shimla":        {"hotel": 1.13, "food": 0.88, "transport": 0.93, "ticket": 0.73, "shopping": 0.93,
                          "note": "Hill capital, seasonal premium"},
        "dharamshala":   {"hotel": 0.93, "food": 0.85, "transport": 0.88, "ticket": 0.68, "shopping": 0.88,
                          "note": "Tibetan culture hub, moderate"},
        "kasol":         {"hotel": 0.73, "food": 0.78, "transport": 0.88, "ticket": 0.48, "shopping": 0.73,
                          "note": "Backpacker Parvati Valley, cheapest stays"},
        "spiti":         {"hotel": 0.83, "food": 0.73, "transport": 1.18, "ticket": 0.58, "shopping": 0.63,
                          "note": "Remote cold desert — transport costs high"},

        # ── Uttarakhand ───────────────────────────────────────────────────────
        "rishikesh":     {"hotel": 0.88, "food": 0.83, "transport": 0.83, "ticket": 0.78, "shopping": 0.83,
                          "note": "Yoga capital — ashrams keep prices down"},
        "haridwar":      {"hotel": 0.78, "food": 0.70, "transport": 0.78, "ticket": 0.63, "shopping": 0.78,
                          "note": "Pilgrimage city, very affordable"},
        "nainital":      {"hotel": 1.03, "food": 0.85, "transport": 0.88, "ticket": 0.73, "shopping": 0.88,
                          "note": "Lake hill station, seasonal premium"},
        "mussoorie":     {"hotel": 1.08, "food": 0.88, "transport": 0.88, "ticket": 0.73, "shopping": 0.90,
                          "note": "Queen of Hills — high weekend demand"},

        # ── Maharashtra ───────────────────────────────────────────────────────
        "mumbai":        {"hotel": 1.48, "food": 1.28, "transport": 1.18, "ticket": 0.98, "shopping": 1.38,
                          "note": "Most expensive Indian metro city"},
        "pune":          {"hotel": 1.18, "food": 1.08, "transport": 1.08, "ticket": 0.83, "shopping": 1.13,
                          "note": "IT city, higher than average"},
        "aurangabad":    {"hotel": 0.88, "food": 0.80, "transport": 0.83, "ticket": 1.18, "shopping": 0.85,
                          "note": "Ajanta-Ellora — ticket costs higher"},
        "lonavala":      {"hotel": 0.98, "food": 0.85, "transport": 0.83, "ticket": 0.68, "shopping": 0.83,
                          "note": "Weekend hill getaway"},
        "mahabaleshwar": {"hotel": 1.08, "food": 0.88, "transport": 0.85, "ticket": 0.70, "shopping": 0.88,
                          "note": "Strawberry hill station, seasonal premium"},

        # ── Delhi / North ─────────────────────────────────────────────────────
        "delhi":         {"hotel": 1.33, "food": 1.13, "transport": 1.13, "ticket": 1.28, "shopping": 1.28,
                          "note": "Capital — Mughal heritage tickets pricier"},
        "agra":          {"hotel": 1.03, "food": 0.85, "transport": 0.98, "ticket": 1.58, "shopping": 0.98,
                          "note": "Taj Mahal — monument tickets very expensive"},
        "varanasi":      {"hotel": 0.88, "food": 0.78, "transport": 0.83, "ticket": 0.78, "shopping": 0.88,
                          "note": "Ghats city, moderate pricing"},
        "amritsar":      {"hotel": 0.88, "food": 0.80, "transport": 0.83, "ticket": 0.58, "shopping": 0.90,
                          "note": "Golden Temple city, affordable pilgrim town"},

        # ── Andaman ───────────────────────────────────────────────────────────
        "andaman":       {"hotel": 1.28, "food": 1.08, "transport": 1.38, "ticket": 1.18, "shopping": 0.98,
                          "note": "Island — ferry & inter-island transport costly"},
        "port blair":    {"hotel": 1.22, "food": 1.03, "transport": 1.28, "ticket": 1.13, "shopping": 0.93,
                          "note": "Andaman capital"},
    }

    @staticmethod
    def calculate_budget_summary(city: str, duration: int, budget_level: str) -> dict:
        budget_lower = budget_level.lower().strip()
        city_lower   = city.lower().strip()

        # ── Step 1: Pick USD base rates per tier ─────────────────────────────
        if "luxury" in budget_lower:
            tier_key = "luxury"
        elif "moderate" in budget_lower:
            tier_key = "moderate"
        else:
            tier_key = "budget"

        usd_rates  = BudgetService.TIER_RATES_USD[tier_key]
        tier_label = tier_key.capitalize()

        # ── Step 2: Convert to live INR ───────────────────────────────────────
        inr_rate = _get_usd_to_inr()
        hotel_rate_inr     = int(usd_rates["hotel"]     * inr_rate)
        food_rate_inr      = int(usd_rates["food"]      * inr_rate)
        transport_rate_inr = int(usd_rates["transport"] * inr_rate)
        ticket_rate_inr    = int(usd_rates["ticket"]    * inr_rate)
        shopping_rate_inr  = int(usd_rates["shopping"]  * inr_rate)

        # ── Step 3: Apply city-specific multiplier ────────────────────────────
        profile   = None
        city_note = f"{city.title()} — {tier_label} tier (standard rates)"
        for key, val in BudgetService.CITY_PROFILES.items():
            if key in city_lower or city_lower.startswith(key):
                profile   = val
                city_note = val.get("note", city_note)
                break

        if profile:
            hotel_rate_inr     = int(hotel_rate_inr     * profile.get("hotel",     1.0))
            food_rate_inr      = int(food_rate_inr       * profile.get("food",      1.0))
            transport_rate_inr = int(transport_rate_inr  * profile.get("transport", 1.0))
            ticket_rate_inr    = int(ticket_rate_inr     * profile.get("ticket",    1.0))
            shopping_rate_inr  = int(shopping_rate_inr   * profile.get("shopping",  1.0))

        # ── Step 4: Compute totals ────────────────────────────────────────────
        accommodation_total = hotel_rate_inr     * duration
        food_total          = food_rate_inr      * duration
        transport_total     = transport_rate_inr * duration
        ticket_total        = ticket_rate_inr    * duration
        shopping_total      = shopping_rate_inr   # one-time budget

        total_cost = accommodation_total + food_total + transport_total + ticket_total + shopping_total

        # ── Step 5: Build descriptive expense items ───────────────────────────
        expenses = [
            {
                "id": "exp-1",
                "category": "Hotel",
                "amount": accommodation_total,
                "label": (
                    f"₹{hotel_rate_inr:,}/night × {duration} night{'s' if duration > 1 else ''} "
                    f"— {city_note}"
                )
            },
            {
                "id": "exp-2",
                "category": "Food",
                "amount": food_total,
                "label": f"₹{food_rate_inr:,}/day × {duration} days — Meals & dining"
            },
            {
                "id": "exp-3",
                "category": "Transport",
                "amount": transport_total,
                "label": f"₹{transport_rate_inr:,}/day × {duration} days — Cabs, autos & local transfers"
            },
            {
                "id": "exp-4",
                "category": "Tickets",
                "amount": ticket_total,
                "label": f"₹{ticket_rate_inr:,}/day × {duration} days — Entry fees & sightseeing"
            },
            {
                "id": "exp-5",
                "category": "Shopping",
                "amount": shopping_total,
                "label": f"₹{shopping_rate_inr:,} one-time — Souvenirs & local market shopping"
            }
        ]

        return {
            "estimated_cost": total_cost,
            "expenses": expenses,
            "inr_per_usd": round(inr_rate, 2),
            "tier": tier_label,
            "breakdown": {
                "accommodation": accommodation_total,
                "food":          food_total,
                "transport":     transport_total,
                "tickets":       ticket_total,
                "shopping":      shopping_total
            }
        }
