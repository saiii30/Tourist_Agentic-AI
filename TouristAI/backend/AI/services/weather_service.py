from agents.weather_agent import get_live_weather,get_mock_weather


def get_weather(city):

    data = get_live_weather(city)

    if not data:
        data = get_mock_weather(city)

    return {

        "condition":data["weather"][0]["main"],

        "description":data["weather"][0]["description"],

        "temperature":data["main"]["temp"],

        "humidity":data["main"]["humidity"],

        "wind":data["wind"]["speed"]
    }