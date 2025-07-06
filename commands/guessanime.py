from utils.anime_api import fetch_valid_anime
from utils.economy_json import update_balance
from PIL import Image, ImageFilter
from discord.ext import commands
from io import BytesIO
import requests
import discord
import asyncio
import aiohttp

class GuessAnime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_players = set()

    async def get_blurred_image(self, image_url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        return None
                    
                    image_data = await resp.read()
                    img = Image.open(BytesIO(image_data))
                    
                    blurred_img = img.filter(ImageFilter.GaussianBlur(radius=7.5))
                    
                    buffer = BytesIO()
                    blurred_img.save(buffer, format='PNG')
                    buffer.seek(0)
                    
                    return buffer
        except Exception as e:
            print(f"Error blurring image: {e}")
            return None

    @commands.command()
    async def guessanime(self, ctx):
        if ctx.author.id in self.active_players:
            return await ctx.send("❌ You're already playing a game! Finish it first.")
        
        self.active_players.add(ctx.author.id)
        try:
            anime_info = await fetch_valid_anime()
            if not anime_info:
                return await ctx.send("❌ Failed to fetch anime data. Try again later.")

            title = anime_info.get('title', 'Unknown Title')
            title_english = anime_info.get('title_english', '')
            score = anime_info.get('score', 'N/A')
            episodes = anime_info.get('episodes', 'Unknown')
            image_url = anime_info.get('image_url', 'https://i.imgur.com/3ZUrjUP.png')
            genres = ', '.join(g['name'] for g in anime_info.get('genres', []))
            formatted_genre = genres[:genres.find(",")] if "," in genres else genres

            blurred_image = await self.get_blurred_image(image_url)

            embed = discord.Embed(
                title="🎲 Guess the Anime!",
                description="Try to guess the anime based on the clues below. You have **5 guesses!**",
                color=0x39FF14
            )

            embed.add_field(name="🧩 Title", value="`???`", inline=True)
            embed.add_field(name="🎭 Genre", value="`???`", inline=True)
            embed.add_field(name="📺 Episodes", value="`???`", inline=True)
            embed.add_field(name="⭐ Score", value="`???`", inline=True)
            embed.add_field(name="🎲 Your Guesses", value="No guesses yet!", inline=False)
            embed.set_footer(text="Type your guess below to begin!")

            if blurred_image:
                file = discord.File(blurred_image, filename="blurred_anime.png")
                embed.set_thumbnail(url="attachment://blurred_anime.png")
                message = await ctx.send(file=file, embed=embed)
            else:
                embed.set_thumbnail(url=image_url)
                message = await ctx.send(embed=embed)

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            attempts = 5
            revealed_score = False
            revealed_genre = False
            revealed_episodes = False
            past_guesses = []
            hint = ""

            while attempts > 0:
                try:
                    guess = await self.bot.wait_for("message", timeout=120.0, check=check)
                except asyncio.TimeoutError:
                    embed.color = 0xFF0000
                    embed.set_field_at(0, name="🧩 Title", value="`???`", inline=True)
                    embed.set_field_at(1, name="🎭 Genre", value="`???`", inline=True)
                    embed.set_field_at(2, name="📺 Episodes", value="`???`", inline=True)
                    embed.set_field_at(3, name="⭐ Score", value="`???`", inline=True)
                    embed.set_field_at(4, name="🎲 Your Guesses", value="⏰ You did not respond in time.", inline=False)
                    return await message.edit(embed=embed)

                correct_titles = [title.lower()]
                if title_english:
                    correct_titles.append(title_english.lower())

                guess_url = f"https://api.jikan.moe/v4/anime?q={guess.content}&limit=1"
                try:
                    guess_response = requests.get(guess_url)
                    if guess_response.status_code == 200:
                        guess_data = guess_response.json().get("data", [])
                        if guess_data:
                            guessed_title = guess_data[0].get("title", "").lower()
                            if guessed_title == title.lower():
                                correct_titles.append(guess.content.lower())
                except:
                    pass

                if guess.content.lower() in correct_titles:
                    success_embed = discord.Embed(
                        title="🎉 Correct!",
                        color=0x008000
                    )
                    success_embed.add_field(name="🧩 Title", value=f"*{title}*", inline=True)
                    if title_english:
                        success_embed.add_field(name="🌐 English Title", value=f"*{title_english}*", inline=True)
                    success_embed.add_field(name="🎭 Genre", value=f"`{formatted_genre}`", inline=True)
                    success_embed.add_field(name="📺 Episodes", value=f"`{episodes}`", inline=True)
                    success_embed.add_field(name="⭐ Score", value=f"{score}⭐", inline=True)
                    guess_history = "\n".join(past_guesses) or "No guesses."
                    success_embed.add_field(name="🎲 Your Guesses", value=guess_history, inline=False)
                    success_embed.set_footer(text="You win! You also got 50 dabloons!")
                    success_embed.set_image(url=image_url)
                    update_balance(ctx.author.id, 50)
                    return await message.edit(embed=success_embed, attachments=[])

                try:
                    guess_url = f"https://api.jikan.moe/v4/anime?q={guess.content}&limit=5"
                    guess_response = requests.get(guess_url)
                    if guess_response.status_code != 200:
                        await ctx.send("❌ Could not reach the API. Try again.")
                        continue

                    guess_data = guess_response.json().get("data", [])
                    matched_anime = next((a for a in guess_data if a.get("title", "").lower() == guess.content.lower()), None)
                    if not matched_anime:
                        matched_anime = next((a for a in guess_data if a.get("type") == "TV"), None)
                    if not matched_anime and guess_data:
                        matched_anime = guess_data[0]
                    if not matched_anime:
                        await ctx.send("❌ Could not find that anime. Try again.")
                        continue

                    guessed_title = matched_anime.get("title")
                    guessed_score = matched_anime.get("score", None)
                    guessed_episodes = matched_anime.get("episodes", None)
                    guessed_genres = ', '.join(g['name'] for g in matched_anime.get('genres', []))
                    guessed_main_genre = guessed_genres[:guessed_genres.find(",")] if "," in guessed_genres else guessed_genres

                    if guessed_score is not None and float(guessed_score) == float(score):
                        revealed_score = True
                    if guessed_main_genre.lower() == formatted_genre.lower():
                        revealed_genre = True
                    if guessed_episodes is None:
                        if revealed_episodes:
                            guessed_episodes = episodes
                        else:
                            guessed_episodes = '❓'
                    elif guessed_episodes == episodes:
                        revealed_episodes = True

                    if guessed_score is not None and score is not None:
                        diff = float(score) - float(guessed_score)
                        if abs(diff) < 0.5:
                            hint = "🟢 Very Close!!"
                            embed.color = 0x008000
                        elif diff > 0:
                            hint = "🟡 The actual score is **higher**"
                            embed.color = 0xFFFF00
                        else:
                            hint = "🔴 The actual score is **lower**"
                            embed.color = 0xFF0000

                    attempts -= 1
                    past_guesses.append(
                        f"- **{guessed_title}** | "
                        f"🎭 `{guessed_main_genre or '❓'}` | "
                        f"📺 `{episodes if revealed_episodes else (guessed_episodes if guessed_episodes != '❓' else '❓')}` | "
                        f"⭐ `{guessed_score or '❓'}`"
                    )
                    guess_history = "\n".join(past_guesses[-5:])
                    embed.description=f"Try to guess the anime based on the clues below. You have **{attempts} guesses!**"
                    embed.set_field_at(0, name="🧩 Title", value="`???`", inline=True)
                    embed.set_field_at(1, name="🎭 Genre", value=f"`{formatted_genre}`" if revealed_genre else "`???`", inline=True)
                    embed.set_field_at(2, name="📺 Episodes", value=f"`{episodes}`" if revealed_episodes else "`???`", inline=True)
                    embed.set_field_at(3, name="⭐ Score", value=f"{score}⭐" if revealed_score else "`???`", inline=True)
                    embed.set_field_at(4, name="🎲 Your Guesses", value=f"{hint}\n\n{guess_history}", inline=False)

                    await message.edit(embed=embed)

                except Exception as e:
                    await ctx.send(f"❌ An error occurred: {str(e)}")
                    continue

            reveal_embed = discord.Embed(
                title="🛑 Out of Attempts!",
                color=0xFF0000
            )
            reveal_embed.add_field(name="🧩 Title", value=f"*{title}*", inline=True)
            if title_english:
                reveal_embed.add_field(name="🌐 English Title", value=f"*{title_english}*", inline=True)
            reveal_embed.add_field(name="🎭 Genre", value=f"`{formatted_genre}`", inline=True)
            reveal_embed.add_field(name="📺 Episodes", value=f"`{episodes}`", inline=True)
            reveal_embed.add_field(name="⭐ Score", value=f"{score}⭐", inline=True)
            guess_history = "\n".join(past_guesses) or "No guesses."
            reveal_embed.add_field(name="🎲 Your Guesses", value=guess_history, inline=False)
            reveal_embed.set_footer(text="Better luck next time!")
            reveal_embed.set_image(url=image_url)
            await message.edit(embed=reveal_embed, attachments=[])

        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")
        finally:
            self.active_players.discard(ctx.author.id)

async def setup(bot):
    await bot.add_cog(GuessAnime(bot))