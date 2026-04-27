import os

import requests

import server.env  # noqa: F401 — ensure `.env` loaded for WEATHER_API_KEY

from server.core.auth import create_authenticated_mcp

weather_mcp = create_authenticated_mcp("Weather", "weather", required_scopes=["mcp:weather"])


@weather_mcp.tool()
async def get_weather(city: str) -> str:
    """
    Get the current weather conditions for a given city.
    """
    params = {
        "key": os.getenv("WEATHER_API_KEY"),
        "q": city,
    }
    response = requests.get("http://api.weatherapi.com/v1/current.json", params=params)

    current_weather = response.json().get("current")
    current_weather_str = (
        f"The current weather in {city} is {current_weather.get('condition').get('text')} "
        f"with a temperature of {current_weather.get('temp_c')}°C and a humidity of "
        f"{current_weather.get('humidity')}%."
    )

    return current_weather_str
