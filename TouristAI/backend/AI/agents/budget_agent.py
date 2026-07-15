from services.budget_service import BudgetService


def budget_agent(
    question: str,
    city: str = "None",
    days: int = 3,
    travelers: int = 1,
    budget_level: str = "Moderate",
    include_hotel: str = "Yes",
    include_transport: str = "Yes",
    shopping_budget: str = "Yes",
):
    if city == "None":
        return {"message": "I need to know the trip city before estimating the budget."}

    try:
        days = int(days)
    except Exception:
        days = 3

    try:
        travelers = max(1, int(travelers))
    except Exception:
        travelers = 1

    summary = BudgetService.calculate_budget_summary(city, days, budget_level)
    breakdown = summary.get("breakdown", {}).copy()

    if include_hotel.lower() == "no":
        breakdown["accommodation"] = 0
    if include_transport.lower() == "no":
        breakdown["transport"] = 0
    if shopping_budget.lower() == "no":
        breakdown["shopping"] = 0

    scaled = {
        "accommodation": breakdown.get("accommodation", 0),
        "food": breakdown.get("food", 0) * travelers,
        "transport": breakdown.get("transport", 0) * travelers,
        "tickets": breakdown.get("tickets", 0) * travelers,
        "shopping": breakdown.get("shopping", 0),
    }
    total = sum(scaled.values())

    expenses = [
        {"id": "budget-hotel", "category": "Hotel", "amount": scaled["accommodation"], "label": "Accommodation"},
        {"id": "budget-food", "category": "Food", "amount": scaled["food"], "label": f"Meals for {travelers} traveler(s)"},
        {"id": "budget-transport", "category": "Transport", "amount": scaled["transport"], "label": "Local transfers"},
        {"id": "budget-tickets", "category": "Tickets", "amount": scaled["tickets"], "label": "Entry tickets and activities"},
        {"id": "budget-shopping", "category": "Shopping", "amount": scaled["shopping"], "label": "Shopping and souvenirs"},
    ]

    saving_tip = "Choose homestays, local buses/autos, and free attractions to reduce the total cost."
    if budget_level.lower() == "luxury":
        saving_tip = "For a luxury trip, keep hotel and private transport flexible because they drive most of the cost."
    elif budget_level.lower() == "moderate":
        saving_tip = "For a moderate trip, mix one premium experience with budget-friendly food and transport."

    lines = [
        f"**Estimated Trip Budget for {city.title()}**",
        "",
        f"Travelers: {travelers}",
        f"Duration: {days} day(s)",
        f"Budget type: {budget_level}",
        "",
        f"* Hotel: ₹{scaled['accommodation']:,}",
        f"* Food: ₹{scaled['food']:,}",
        f"* Transport: ₹{scaled['transport']:,}",
        f"* Tickets: ₹{scaled['tickets']:,}",
        f"* Shopping: ₹{scaled['shopping']:,}",
        "",
        f"**Total Estimated Cost: ₹{total:,}**",
        "",
        f"Suggestion: {saving_tip}",
    ]

    return {
        "source": "budget_service",
        "answer": "\n".join(lines),
        "data": {
            "estimated_cost": total,
            "expenses": expenses,
            "breakdown": scaled,
            "travelers": travelers,
            "duration": days,
            "budget_level": budget_level,
        },
    }
