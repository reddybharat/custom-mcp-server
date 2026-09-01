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


@weather_mcp.resource("resource://weather/capabilities", mime_type="text/plain")
async def weather_capabilities() -> str:
    """Reference text describing Weather MCP tools (for clients that load resources)."""
    return (
        "Weather MCP tools (require scope mcp:weather):\n"
        "- get_weather(city: str) -> str: current conditions from WeatherAPI "
        "(temperature °C, condition text, humidity). Requires WEATHER_API_KEY on the server.\n"
    )


@weather_mcp.prompt(
    name="weather_assistant",
    title="Weather assistant",
    description="Bootstrap messages for weather questions; optional city for context.",
)
async def weather_assistant(city: str | None = None) -> str:
    if city:
        return (
            "You are helping with weather information via the Weather MCP server. "
            f"The user is interested in: {city}. "
            "Call get_weather with the city name when they need current conditions."
        )
    return (
        "You are helping with weather information via the Weather MCP server. "
        "When the user names a city, call get_weather(city) for current conditions."
    )
