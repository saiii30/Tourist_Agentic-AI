from datetime import datetime

from services.weather_service import get_weather
from services.holiday_service import is_holiday
from services.season_service import get_current_season
from services.event_service import has_event


def predict_crowd(

        city,

        popularity,

        best_visit_time

):

    weather = get_weather(city)

    event,event_name = has_event(city)

    holiday = is_holiday()

    season = get_current_season()

    score = 0

    reasons=[]

    ##################################################

    # Popularity

    ##################################################

    if popularity=="Popular":

        score+=5

        reasons.append("Popular tourist attraction")

    elif popularity=="Medium":

        score+=3

        reasons.append("Moderately popular attraction")

    else:

        score+=1

        reasons.append("Hidden attraction")

    ##################################################

    # Weekend

    ##################################################

    weekday=datetime.now().weekday()

    if weekday>=5:

        score+=2

        reasons.append("Weekend")

    ##################################################

    # Holiday

    ##################################################

    if holiday:

        score+=3

        reasons.append("Public Holiday")

    ##################################################

    # Festival

    ##################################################

    if event:

        score+=4

        reasons.append(event_name)

    ##################################################

    # Weather

    ##################################################

    condition=weather["condition"].lower()

    if "rain" in condition:

        score-=3

        reasons.append("Rain")

    elif "storm" in condition:

        score-=5

        reasons.append("Storm")

    elif "clear" in condition:

        score+=2

        reasons.append("Pleasant weather")

    ##################################################

    # Season

    ##################################################

    if season=="Winter":

        score+=2

        reasons.append("Peak Tourism Season")

    elif season=="Monsoon":

        score-=1

        reasons.append("Monsoon Season")

    ##################################################

    # Time

    ##################################################

    hour=datetime.now().hour

    if 8<=hour<=11:

        score+=2

        reasons.append("Morning visiting hours")

    elif 17<=hour<=20:

        score+=3

        reasons.append("Evening peak hours")

    ##################################################

    # Best Visit Time

    ##################################################

    if best_visit_time.lower()=="morning":

        if 8<=hour<=11:

            score+=1

            reasons.append("Ideal visiting time")

    ##################################################

    # Final Result

    ##################################################

    if score>=14:

        crowd="Very High"

        emoji="🔴"

        advice="Visit before 8 AM or after 6 PM."

    elif score>=10:

        crowd="High"

        emoji="🟠"

        advice="Expect queues. Book tickets early."

    elif score>=6:

        crowd="Medium"

        emoji="🟡"

        advice="Moderate crowd expected."

    else:

        crowd="Low"

        emoji="🟢"

        advice="Best time for a peaceful visit."

    return{

        "crowd":crowd,

        "emoji":emoji,

        "score":score,

        "weather":weather,

        "reasons":reasons,

        "advice":advice
    }




# """
# Crowd predictor — now blends 3-year historical baseline with live signals.

# Backward compatible:
#     predict_crowd(city, popularity, best_visit_time)                # old callers
#     predict_crowd(city, popularity, best_visit_time, attraction)    # new

# Scoring:
#     final_score = 0.6 * historical_score + 0.4 * live_score
#     (falls back to 100% live_score if attraction has no history)

# Live score reuses all your existing signals: popularity, weekend,
# holiday, event, weather, season, hour, best_visit_time.
# """

# from datetime import datetime

# from services.weather_service import get_weather
# from services.holiday_service import is_holiday
# from services.season_service import get_current_season
# from services.event_service import has_event
# from services.crowd_history_service import get_history_score


# def _live_score(city, popularity, best_visit_time):
#     weather = get_weather(city)
#     event, event_name = has_event(city)
#     holiday = is_holiday()
#     season = get_current_season()

#     score = 0
#     reasons = []

#     # popularity
#     if popularity == "Popular":
#         score += 5; reasons.append("Popular tourist attraction")
#     elif popularity == "Medium":
#         score += 3; reasons.append("Moderately popular attraction")
#     else:
#         score += 1; reasons.append("Hidden attraction")

#     # weekend
#     if datetime.now().weekday() >= 5:
#         score += 2; reasons.append("Weekend")

#     # holiday
#     if holiday:
#         score += 3; reasons.append("Public Holiday")

#     # event
#     if event:
#         score += 4; reasons.append(event_name)

#     # weather
#     condition = (weather.get("condition") or "").lower()
#     if "rain" in condition:
#         score -= 3; reasons.append("Rain")
#     elif "storm" in condition:
#         score -= 5; reasons.append("Storm")
#     elif "clear" in condition:
#         score += 2; reasons.append("Pleasant weather")

#     # season
#     if season == "Winter":
#         score += 2; reasons.append("Peak tourism season")
#     elif season == "Monsoon":
#         score -= 1; reasons.append("Monsoon season")

#     # hour
#     hour = datetime.now().hour
#     if 8 <= hour <= 11:
#         score += 2; reasons.append("Morning visiting hours")
#     elif 17 <= hour <= 20:
#         score += 3; reasons.append("Evening peak hours")

#     # best time match
#     if best_visit_time and best_visit_time.lower() == "morning" and 8 <= hour <= 11:
#         score += 1; reasons.append("Ideal visiting time")

#     return score, reasons, weather


# def _bucket(score):
#     if score >= 14: return "Very High", "🔴", "Visit before 8 AM or after 6 PM."
#     if score >= 10: return "High",      "🟠", "Expect queues. Book tickets early."
#     if score >= 6:  return "Medium",    "🟡", "Moderate crowd expected."
#     return              "Low",       "🟢", "Best time for a peaceful visit."


# def predict_crowd(city, popularity, best_visit_time, attraction=None):
#     live_score, reasons, weather = _live_score(city, popularity, best_visit_time)

#     history = get_history_score(city, attraction) if attraction else None

#     if history:
#         # scale history 0..10 -> 0..20 to match live scale, then blend
#         hist_scaled = history["history_score"] * 2
#         final = round(0.6 * hist_scaled + 0.4 * live_score)
#         reasons.insert(
#             0,
#             f"3-yr history: {history['ratio']}× normal for this slot",
#         )
#     else:
#         final = live_score

#     crowd, emoji, advice = _bucket(final)

#     return {
#         "crowd":   crowd,
#         "emoji":   emoji,
#         "score":   final,
#         "weather": weather,
#         "reasons": reasons,
#         "advice":  advice,
#         "history": history,   # None if no records
#     }
