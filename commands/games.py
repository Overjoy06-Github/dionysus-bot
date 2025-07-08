from utils.anime_api import fetch_valid_anime
from utils.economy_json import update_balance
from PIL import Image, ImageFilter
from discord.ext import commands
from io import BytesIO
import discord
import asyncio
import aiohttp
import string
import random

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_players = set()
        self.common_words = None

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

    async def fetch_jikan_data(self, url, retries=3, timeout=10):
        async with aiohttp.ClientSession() as session:
            for attempt in range(retries):
                try:
                    async with session.get(url, timeout=timeout) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:
                            await asyncio.sleep(2 ** attempt)
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt == retries - 1:
                        raise
                    await asyncio.sleep(1)
            return None
        
    @commands.command()
    async def guessanime(self, ctx):
        if ctx.author.id in self.active_players:
            return await ctx.send("❌ You're already playing a game! Finish it first.")
        
        self.active_players.add(ctx.author.id)
        type_emojis = {
            "TV": "📺",
            "Movie": "🎬",
            "OVA": "📀",
            "ONA": "🌐",
            "TV Special": "🎉",
            "Special": "🎉",
            "Music": "🎵",
            "PV": "📣",
            "CM": "📢",
            "Unknown": "❓"
        }

        try:
            anime_info = await fetch_valid_anime()
            if not anime_info:
                return await ctx.send("❌ Failed to fetch anime data. Try again later.")

            title = anime_info.get('title', 'Unknown Title')
            title_english = anime_info.get('title_english', '')
            anime_type = anime_info.get('type', 'Unknown')
            score = anime_info.get('score', 'N/A')
            episodes = anime_info.get('episodes', 'Unknown')
            image_url = anime_info.get('image_url', 'https://i.imgur.com/3ZUrjUP.png')
            genres = ', '.join(g['name'] for g in anime_info.get('genres', [])) if anime_info.get('genres') else 'None'
            formatted_genre = genres[:genres.find(",")] if "," in genres else genres

            type_emoji = type_emojis.get(anime_type, "❓")
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
            embed.add_field(name="❓ Type", value="`???`", inline=True)
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
            revealed_type = False
            past_guesses = []
            hint = ""

            while attempts > 0:
                try:
                    guess = await self.bot.wait_for("message", timeout=120.0, check=check)
                except asyncio.TimeoutError:
                    embed.color = 0xFF0000
                    embed.set_field_at(0, name="🧩 Title", value=f"*{title}*", inline=True)
                    if title_english:
                        embed.add_field(name="🌐 English Title", value=f"*{title_english}*", inline=True)
                    embed.set_field_at(1, name="🎭 Genre", value=f"`{formatted_genre}`", inline=True)
                    embed.set_field_at(2, name="📺 Episodes", value=f"`{episodes}`", inline=True)
                    embed.set_field_at(3, name="⭐ Score", value=f"`{score}`", inline=True)
                    embed.set_field_at(4, name=f"{type_emoji} Type", value=f"`{anime_type}`", inline=True)
                    embed.set_field_at(5, name="🎲 Your Guesses", value="⏰ You did not respond in time.", inline=False)
                    embed.set_image(url=image_url)
                    return await message.edit(embed=embed, attachments=[])

                correct_titles = [title.lower()]
                if title_english:
                    correct_titles.append(title_english.lower())

                guess_url = f"https://api.jikan.moe/v4/anime?q={guess.content}&limit=1"
                try:
                    guess_response = await self.fetch_jikan_data(guess_url)
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
                    success_embed.add_field(name="⭐ Score", value=f"`{score}⭐`", inline=True)
                    success_embed.add_field(name=f"{type_emoji} Type", value=f"`{anime_type}`", inline=True)
                    guess_history = "\n".join(past_guesses) or "No guesses."
                    success_embed.add_field(name="🎲 Your Guesses", value=guess_history, inline=False)
                    success_embed.set_footer(text="You win! You also got 50 Dionysus coins!")
                    success_embed.set_image(url=image_url)
                    update_balance(ctx.author.id, 50)
                    return await message.edit(embed=success_embed, attachments=[])

                try:
                    guess_url = f"https://api.jikan.moe/v4/anime?q={guess.content}&limit=5"
                    guess_response = await self.fetch_jikan_data(guess_url)

                    if guess_response and 'data' in guess_response:
                        guess_data = guess_response['data']

                        matched_anime = next((a for a in guess_data if a.get("title", "").lower() == guess.content.lower()), None)
                        if not matched_anime:
                            matched_anime = next((a for a in guess_data if a.get("type") == "TV"), None)
                        if not matched_anime and guess_data:
                            matched_anime = guess_data[0]
                        if not matched_anime:
                            await ctx.send("❌ Could not find that anime. Try again.")
                            continue

                        guessed_title = matched_anime.get("title")
                        guessed_type = matched_anime.get("type", "Unknown")
                        guessed_type_emoji = type_emojis.get(guessed_type, "❓")
                        guessed_score = matched_anime.get("score", None)
                        guessed_episodes = matched_anime.get("episodes", None)
                        guessed_genres = ', '.join(g['name'] for g in matched_anime.get('genres', [])) if matched_anime.get("genres") else "None"
                        guessed_main_genre = guessed_genres[:guessed_genres.find(",")] if "," in guessed_genres else guessed_genres

                        if guessed_score is not None and score != 'N/A':
                            if float(guessed_score) == float(score):
                                revealed_score = True
                        if guessed_type.lower() == anime_type.lower():
                            revealed_type = True
                        if guessed_main_genre.lower() == formatted_genre.lower():
                            revealed_genre = True
                        if guessed_episodes is not None and str(guessed_episodes) == str(episodes):
                            revealed_episodes = True

                        if guessed_score is not None and score != 'N/A':
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
                            f"⭐ `{guessed_score or '❓'}` | {guessed_type_emoji} {guessed_type}"
                        )
                        guess_history = "\n".join(past_guesses[-5:])
                        embed.description=f"Try to guess the anime based on the clues below. You have **{attempts} guesses!**"
                        embed.set_field_at(0, name="🧩 Title", value="`???`", inline=True)
                        embed.set_field_at(1, name="🎭 Genre", value=f"`{formatted_genre}`" if revealed_genre else "`???`", inline=True)
                        embed.set_field_at(2, name="📺 Episodes", value=f"`{episodes}`" if revealed_episodes else "`???`", inline=True)
                        embed.set_field_at(3, name="⭐ Score", value=f"`{score}⭐`" if revealed_score else "`???`", inline=True)
                        embed.set_field_at(4, name=f"{type_emoji} Type" if revealed_type else '❓', value=f"{anime_type}" if revealed_type else "`???`", inline=True)
                        embed.set_field_at(5, name="🎲 Your Guesses", value=f"{hint}\n\n{guess_history}", inline=False)

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
            reveal_embed.add_field(name="⭐ Score", value=f"`{score}⭐`", inline=True)
            reveal_embed.add_field(name=f"{type_emoji} Type", value=f"`{anime_type}`", inline=True)
            guess_history = "\n".join(past_guesses) or "No guesses."
            reveal_embed.add_field(name="🎲 Your Guesses", value=guess_history, inline=False)
            reveal_embed.set_footer(text="Better luck next time!")
            reveal_embed.set_image(url=image_url)
            await message.edit(embed=reveal_embed, attachments=[])

        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")
        finally:
            self.active_players.discard(ctx.author.id)

    async def is_valid_word(self, word):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}") as response:
                    return response.status == 200
        except:
             return False
        
    async def get_random_valid_word(self):
        if not self.common_words:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt") as resp:
                        if resp.status == 200:
                            text = await resp.text()
                            words = [w.lower() for w in text.splitlines() if len(w) == 5]
                            self.common_words = words
            except:
                self.common_words = None

        if self.common_words:
            for _ in range(5):
                word = random.choice(self.common_words)
                if await self.is_valid_word(word):
                    return word

        letters = string.ascii_lowercase
        for _ in range(10):
            word = ''.join(random.choice(letters) for _ in range(5))
            if await self.is_valid_word(word):
                return word
        
        return random.choice(['apple', 'brave', 'crane', 'dance', 'eagle'])
    
    @commands.command(aliases=['wordgame', 'guessword', 'wordpuzzle', 'wrdl'])
    async def wordle(self, ctx):
        if ctx.author.id in self.active_players:
            return await ctx.send("❌ You're already playing a game! Finish it first.", delete_after=3)
        
        self.active_players.add(ctx.author.id)
        try:
            current_word = await self.get_random_valid_word()
            if not current_word:
                return await ctx.send("❌ Failed to get a valid word. Please try again later.")
            
            guesses = []
            embed = discord.Embed(
                title="Wordle!",
                description="Try to guess the word based on the clues below. You have **5 guesses!**",
                color=0x39FF14
            )

            for _ in range(6):
                embed.add_field(name='', value=":black_medium_square:"*5, inline=False)
            embed.set_footer(text="Type your guess below to begin!")
            message = await ctx.send(embed=embed)

            def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel
            
            attempts = 6
            while attempts > 0:
                    try:
                        guess = await self.bot.wait_for("message", timeout=120.0, check=check)
                    except asyncio.TimeoutError:
                        embed.color = 0xFF0000
                        embed.description= "⏰ You did not respond in time."
                        return await message.edit(embed=embed)
                    
                    guess_content = guess.content.lower()

                    if len(guess_content) != 5:
                         await ctx.send("❌ You must use a word that's 5 letters long.", delete_after=3)
                         continue
                    
                    if not await self.is_valid_word(guess_content):
                        await ctx.send("❌ That's not a valid English word.", delete_after=3)
                        continue

                    if not await self.is_valid_word(guess_content):
                        await ctx.send("❌ That's not a valid English word.", delete_after=3)
                        continue

                    attempts -= 1
                    guesses.append(guess_content)

                    embed.clear_fields()
                    for guess in guesses:
                        line = []
                        target_letters = list(current_word)
                        guess_letters = list(guess)
                        
                        for i in range(len(guess_letters)):
                            if guess_letters[i] == target_letters[i]:
                                line.append("🟩")
                                target_letters[i] = None
                                guess_letters[i] = None
                            else:
                                line.append("")
                        
                        for i in range(len(guess_letters)):
                            if guess_letters[i] is not None:
                                if guess_letters[i] in target_letters:
                                    line[i] = "🟨"
                                    target_letters[target_letters.index(guess_letters[i])] = None
                                else:
                                    line[i] = "⬛"
                        
                        embed.add_field(name='', value=f"{''.join(line)} {guess.upper()}", inline=False)

                    for _ in range(6 - len(guesses)):
                        embed.add_field(name='', value="⬛⬛⬛⬛⬛", inline=False)
                    
                    await message.edit(embed=embed)
                    if guess_content == current_word:
                        embed.color = 0x39FF14
                        embed.description = f"🎉 You won! The word was **{current_word.upper()}**"
                        embed.add_field(name="Reward", value="<:dionysus_coin:1391088284825948273> You won 100 Dionysus Coins!")
                        update_balance(ctx.author.id, 100)
                        return await message.edit(embed=embed)
            embed.color = 0xFF0000
            embed.description = f"😢 You lost! The word was **{current_word.upper()}**"
            await message.edit(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {e}")
        finally:
            self.active_players.discard(ctx.author.id)

async def setup(bot):
    await bot.add_cog(Games(bot))
