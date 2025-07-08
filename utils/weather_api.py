import aiohttp
import os

TOKEN = os.environ.get("WEATHER_TOKEN")

async def search_weather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&APPID={TOKEN}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

                return {
                    'weather': data.get("weather"),
                    'stats': data.get("main"),
                    'country': data.get("sys", {}).get("country"),
                    'city': data.get("name")
                }
    except:
        return []
