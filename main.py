from utils.stocks_prices import update_all_company_prices
from commands import setup as setup_commands
from discord import ActivityType
from discord.ext import commands
import asyncio
import discord
import random
import os

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)
dionysus_moods = [
    {"type": ActivityType.playing, "name": "with mortal sanity 🍇"},
    {"type": ActivityType.listening, "name": "drunken hymns"},
    {"type": ActivityType.watching, "name": "grapevines grow"},
    {"type": ActivityType.streaming, "name": "Live from Mount Olympus", "url": "https://twitch.tv/godofwine"}
]

async def rotate_presence():
    while True:
        mood = random.choice(dionysus_moods)
        await bot.change_presence(activity=discord.Activity(**mood))
        await asyncio.sleep(300)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    bot.loop.create_task(rotate_presence())
    bot.loop.create_task(update_all_company_prices("data/companies.json"))
    await setup_commands(bot)


if __name__ == "__main__":
    bot.run(os.environ["BOT_TOKEN"])
