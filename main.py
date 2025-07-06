import discord
from discord.ext import commands
import os
from commands import setup as setup_commands

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    await setup_commands(bot)

if __name__ == "__main__":
    bot.run(os.environ["BOT_TOKEN"])