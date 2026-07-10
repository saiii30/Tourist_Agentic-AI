from datetime import datetime

from services.weather_service import get_weather
from services.holiday_service import is_holiday
from services.season_service import get_current_season
from services.event_service import has_event


def predict_crowd(

        city,

        popularity,

        best_visit_time,

      attraction=None
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



