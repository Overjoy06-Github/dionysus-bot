from utils.economy_json import update_balance
from discord.ext import commands
import discord
import asyncio
import aiohttp
import random
import string

class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_players = set()
        self.common_words = None

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
    await bot.add_cog(Wordle(bot))
