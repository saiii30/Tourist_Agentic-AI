class BudgetService:
    @staticmethod
    def calculate_budget_summary(city: str, duration: int, budget_level: str) -> dict:
        budget_lower = budget_level.lower()
        city_lower = city.lower()
        
        # Base daily rates based on budget tier
        if "moderate" in budget_lower:
            hotel_rate = 5500
            food_rate = 1200
            transport_rate = 1000
            ticket_rate = 250
            shopping_rate = 1000
        elif "luxury" in budget_lower:
            hotel_rate = 12500
            food_rate = 3000
            transport_rate = 2500
            ticket_rate = 600
            shopping_rate = 3000
        else: # Budget tier
            hotel_rate = 1800
            food_rate = 500
            transport_rate = 400
            ticket_rate = 100
            shopping_rate = 500

        # Adjust for specific cities if needed
        if "goa" in city_lower:
            # Goa has higher transport/misc cost
            transport_rate = int(transport_rate * 1.3)
            hotel_rate = int(hotel_rate * 1.1)
        elif "ooty" in city_lower:
            # Ooty has slightly higher hotel rates due to seasonal peak demand
            hotel_rate = int(hotel_rate * 1.2)
            
        accommodation_total = hotel_rate * duration
        food_total = food_rate * duration
        transport_total = transport_rate * duration
        ticket_total = ticket_rate * duration
        shopping_total = shopping_rate

        total_cost = accommodation_total + food_total + transport_total + ticket_total + shopping_total
        
        expenses = [
            {"id": "exp-1", "category": "Hotel", "amount": accommodation_total, "label": f"{hotel_rate}/night accommodation"},
            {"id": "exp-2", "category": "Food", "amount": food_total, "label": f"Dining & meals for {duration} days"},
            {"id": "exp-3", "category": "Transport", "amount": transport_total, "label": "Taxis, autos & local transfers"},
            {"id": "exp-4", "category": "Tickets", "amount": ticket_total, "label": "Monument and sightseeing entry fees"},
            {"id": "exp-5", "category": "Shopping", "amount": shopping_total, "label": "Local souvenir shopping budget"}
        ]
        
        return {
            "estimated_cost": total_cost,
            "expenses": expenses,
            "breakdown": {
                "accommodation": accommodation_total,
                "food": food_total,
                "transport": transport_total,
                "tickets": ticket_total,
                "shopping": shopping_total
            }
        }
