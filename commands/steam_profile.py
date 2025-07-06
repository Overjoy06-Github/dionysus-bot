import requests
import re
from discord.ext import commands
import discord
import os
STEAM_API_KEY = os.environ.get("STEAM_TOKEN")

def is_steamid64(input_str):
    return bool(re.fullmatch(r"\d{17}", input_str))

def get_player_summary(steamid64):
    url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
    params = {
        "key": STEAM_API_KEY,
        "steamids": steamid64
    }
    response = requests.get(url, params=params)
    return response.json()

def resolve_vanity_url(username):
    url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
    params = {
        "key": STEAM_API_KEY,
        "vanityurl": username
    }
    response = requests.get(url, params=params)
    return response.json()

class Steam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def steam(self, ctx, *, query):
        try:
            if is_steamid64(query):
                data = get_player_summary(query)
            else:
                resolved = resolve_vanity_url(query)
                if resolved["response"]["success"] != 1:
                    return await ctx.send("❌ Could not resolve username to SteamID64.")
                steamid64 = resolved["response"]["steamid"]
                data = get_player_summary(steamid64)

            players = data.get("response", {}).get("players", [])
            if not players:
                return await ctx.send("❌ No Steam profile found.")

            player = players[0]
            embed = discord.Embed(
                title=player.get("personaname", "Unknown"),
                url=player.get("profileurl", ""),
                description="Steam Profile Information",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=player.get("avatarfull", ""))
            embed.add_field(name="SteamID64", value=player.get("steamid", "N/A"), inline=False)
            embed.add_field(name="Real Name", value=player.get("realname", "N/A"), inline=False)
            embed.add_field(name="Country", value=player.get("loccountrycode", "N/A"), inline=False)
            embed.set_footer(text="Steam API Lookup")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Steam(bot))