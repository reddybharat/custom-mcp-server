from mcp.server.fastmcp import FastMCP
import requests
import os
from dotenv import load_dotenv
load_dotenv()

mcp = FastMCP("Weather")

@mcp.tool()
async def get_weather(city: str) -> str:
    """
    Get the current weather conditions for a given city.
    """
    params = {
        'key': os.getenv('WEATHER_API_KEY'),
        'q': city,
    }
    response = requests.get(f"http://api.weatherapi.com/v1/current.json", params=params)

    current_weather = response.json().get('current')
    current_weather_str = f"The current weather in {city} is {current_weather.get('condition').get('text')} with a temperature of {current_weather.get('temp_c')}°C and a humidity of {current_weather.get('humidity')}%."
    print(current_weather_str)

    return current_weather_str

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
    # get_weather("Tokyo")