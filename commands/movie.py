import discord
from discord.ext import commands
import requests
import os

class Movie(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['imdb', 'film', 'cinema'])
    async def movie(self, ctx, *, title):
        api_key = os.environ.get("OMDB_TOKEN")
        if not api_key:
            return await ctx.send("❌ OMDB API key not configured. Please set the OMDB_TOKEN environment variable.")

        try:
            movie_details = self.search_movie(title, api_key)
            if not movie_details:
                return await ctx.send("❌ Movie not found or error occurred.")
            
            embed = self.create_movie_embed(movie_details)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")

    def search_movie(self, title, api_key):
        base_url = "http://www.omdbapi.com/"
        params = {
            "apikey": api_key,
            "t": title,
            "r": "json"
        }
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("Response") == "True":
            return data
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
    await bot.add_cog(Movie(bot))