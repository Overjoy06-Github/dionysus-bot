from discord.ext import commands
import aiohttp
import discord
import re
import os

STEAM_API_KEY = os.environ.get("STEAM_TOKEN")

def is_steamid64(input_str):
    return bool(re.fullmatch(r"\d{17}", input_str))

class Steam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_player_summary(self, steamid64):
        url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
        params = {
            "key": STEAM_API_KEY,
            "steamids": steamid64
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                return await response.json()

    async def resolve_vanity_url(self, username):
        url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
        params = {
            "key": STEAM_API_KEY,
            "vanityurl": username
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                return await response.json()

    @commands.command()
    async def steam(self, ctx, *, query):
        try:
            if is_steamid64(query):
                data = await self.get_player_summary(query)
            else:
                resolved = await self.resolve_vanity_url(query)
                if resolved["response"]["success"] != 1:
                    return await ctx.send("❌ Could not resolve username to SteamID64.")
                steamid64 = resolved["response"]["steamid"]
                data = await self.get_player_summary(steamid64)

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
            
            if "timecreated" in player:
                from datetime import datetime
                created = datetime.fromtimestamp(player["timecreated"])
                embed.add_field(name="Account Created", value=created.strftime("%B %d, %Y"), inline=False)
            
            embed.set_footer(text="Steam API Lookup")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Steam(bot))
