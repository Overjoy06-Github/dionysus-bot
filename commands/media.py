from utils.weather_api import search_weather
from utils.paginator import AnimePaginator
from utils.anime_api import search_anime
from discord.ext import commands
import discord
import aiohttp
import os

class Weather_and_Media(commands.Cog, name="Weather & Media"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def anime(self, ctx, *, query):
        try:
            anime_list = await search_anime(query)
            if not anime_list:
                return await ctx.send("❌ No anime found with that name.")
            
            view = AnimePaginator(anime_list)
            await ctx.send(embed=view.get_embed(), view=view)
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")

    def kelvin_to_celsius(self, kelvin):
        celsius = round(kelvin - 273.15, 1)
        return celsius

    def get_temperature_emoji(self, temp):
        if temp >= 35.0: return "🔥"
        elif 30 <= temp < 35: return "☀️"
        elif 25 <= temp < 30: return "🌤️"
        elif 18 <= temp < 25: return "🌥️"
        elif 10 <= temp < 18: return "❄️"
        elif 0 <= temp < 10: return "🥶"
        else: return "🧊"

    async def get_country_info(self, country_code):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://restcountries.com/v3.1/alpha/{country_code.lower()}") as response:
                    data = await response.json()
                    return {
                        'official_name': data[0]['name']['official'],
                        'flag': data[0]['flag'],
                        'maps': data[0]['maps']['googleMaps']
                    }
        except:
            return None
        
    @commands.command(aliases=['w', 'forecast'])
    async def weather(self, ctx, *, city: str = None):
        if not city:
            return await ctx.send("❌ Please specify a city. Example: `!weather Manila`")
        
        try:
            weather_data = await search_weather(city.lower())
            if not weather_data:
                return await ctx.send(f"❌ City '{city}' not found. Please check the spelling.")
            
            stats = weather_data['stats']
            city_name = weather_data['city'].title()
            country = weather_data['country']

            country_info = await self.get_country_info(country)
            if country_info:
                country_display = f"{country_info['official_name']} {country_info['flag']}"
                country_url = country_info['maps']
            else:
                country_display = country
                country_url = None

            current_temp = self.kelvin_to_celsius(stats['temp'])
            feels_like = self.kelvin_to_celsius(stats['feels_like'])
            temp_min = self.kelvin_to_celsius(stats['temp_min'])
            temp_max = self.kelvin_to_celsius(stats['temp_max'])

            emoji = self.get_temperature_emoji(feels_like)
            weather_desc = weather_data['weather'][0]['description'].title()

            embed = discord.Embed(
                title=f"{city_name}, {country_display}",
                description=f"# 🌤️ Weather Basics\n-# {weather_desc}\n## What is hPa\n- hPa (hectopascals) measure air pressure:\n  * 1013 hPa = Average sea-level pressure\n  * Below 1000 hPa = Stormy weather likely\n  * Above 1020 hPa = Clear skies expected",
                url=country_url if country_url else None,
                color=0x3498db,
                timestamp=ctx.message.created_at
            )

            embed.set_thumbnail(url=f"https://openweathermap.org/img/wn/{weather_data['weather'][0]['icon']}@2x.png")

            embed.add_field(
                name="`🌡️ Temperature`",
                value=(
                    f"```elixir\n{emoji} Feels like {feels_like}°C\n"
                    f"  - Current {current_temp}°C\n"
                    f"  - Min/Max: {temp_min}°C | {temp_max}°C```"
                ),
                inline=False
            )

            embed.add_field(
                name="`📊 Conditions`",
                value=(
                    f"```elixir\n💦 Humidity: {stats['humidity']}%\n"
                    f"🗜 Pressure: {stats['pressure']} hPa\n"
                    f"🌊 Sea Level: {stats['sea_level']} hPa\n"
                    f"🏔 Ground Level: {stats['grnd_level']} hPa```"
                ),
                inline=False
            )

            await ctx.send(embed=embed)
            
        except KeyError as e:
            await ctx.send(f"❌ Missing weather data: {str(e)}")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while fetching weather data: {str(e)}")

    @commands.command(aliases=['imdb', 'film', 'cinema'])
    async def movie(self, ctx, *, title):
        api_key = os.environ.get("OMDB_TOKEN")
        if not api_key:
            return await ctx.send("❌ OMDB API key not configured. Please set the OMDB_TOKEN environment variable.")

        try:
            movie_details = await self.search_movie(title, api_key)
            if not movie_details:
                return await ctx.send("❌ Movie not found or error occurred.")
            
            embed = self.create_movie_embed(movie_details)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")

    async def search_movie(self, title, api_key):
        base_url = "http://www.omdbapi.com/"
        params = {
            "apikey": api_key,
            "t": title,
            "r": "json"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if data.get("Response") == "True":
                        return data
                    return None
        except:
            return None

    def create_movie_embed(self, movie_data):
        embed = discord.Embed(
            title=f"{movie_data.get('Title', 'N/A')} ({movie_data.get('Year', 'N/A')})",
            description=f"```elixir\n{movie_data.get('Plot', 'No plot available')}```",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="IMDb Rating", value=f'`{movie_data.get("imdbRating", "N/A")}`', inline=True)
        embed.add_field(name="Runtime", value=f'`{movie_data.get("Runtime", "N/A")}`', inline=True)
        embed.add_field(name="Genres", value=f'`{movie_data.get("Genre", "N/A")}`', inline=True)
        
        if "Director" in movie_data and movie_data["Director"] != "N/A":
            embed.add_field(name="Directors", value=f'`{movie_data["Director"]}`', inline=True)
        if "Actors" in movie_data and movie_data["Actors"] != "N/A":
            embed.add_field(name="Cast", value=f'`{movie_data["Actors"]}`', inline=True)
        
        if "Poster" in movie_data and movie_data["Poster"] != "N/A":
            embed.set_thumbnail(url=movie_data["Poster"])
        
        if "BoxOffice" in movie_data and movie_data["BoxOffice"] != "N/A":
            embed.add_field(name="Box Office", value=f'`{movie_data.get("BoxOffice", "N/A")}`', inline=True)
        if "Awards" in movie_data and movie_data["Awards"] != "N/A":
            embed.add_field(name="Awards", value=f'```elixir\n{movie_data.get("Awards", "N/A")}```', inline=False)
        return embed

async def setup(bot):
    await bot.add_cog(Weather_and_Media(bot))
