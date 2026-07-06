from intelligence.hidden_gems import get_hidden_gems
from services.city_resolver import resolve_city

def hidden_gems_agent(question, city):

    city = resolve_city(city)
    gems = get_hidden_gems(question, city)

    answer = "🌟 Hidden Gems Recommendations\n\n"

    for place in gems:

        answer += f"📍 {place[0]} ({place[1]})\n"

        if place[2]:
            for gem in place[2]:
                answer += f"   • {gem}\n"

        answer += "\n"

    return answer