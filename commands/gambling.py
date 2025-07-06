from discord.ext import commands
import discord
import random
from utils.economy_json import get_balance, update_balance, load_balances

class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['slot'])
    async def slots(self, ctx, bet: float):
        if bet <= 0:
            return await ctx.send("❌ Bet must be greater than 0!")
        
        user_balance = get_balance(ctx.author.id)
        if user_balance < bet:
            formatted_balance = "{:,.2f}".format(user_balance)
            return await ctx.send(f"❌ You don't have enough coins! (Balance: {formatted_balance})")
        
        update_balance(ctx.author.id, -bet)
        
        slots = ["🍒", "🍋", "🍊", "🍇", "🔔", "💎", "7️⃣"]
        result = [random.choice(slots) for _ in range(3)]
        
        if len(set(result)) == 1:
            multiplier = 5
        elif len(set(result)) == 2:
            multiplier = 2
        else:
            multiplier = 0
        
        winnings = bet * multiplier
        
        if winnings > 0:
            update_balance(ctx.author.id, winnings)
        
        formatted_bet = "{:,.2f}".format(bet)
        formatted_winnings = "{:,.2f}".format(winnings) if winnings > 0 else "0.00"
        
        embed = discord.Embed(
            title="🎰 Slot Machine",
            description=f"{' | '.join(result)}\n\n**Bet:** {formatted_bet} coins",
            color=0x00ff00 if winnings > 0 else 0xff0000
        )
        
        if multiplier == 5:
            embed.add_field(name="JACKPOT!", value=f"🎉 Won {formatted_winnings} coins! (5×)", inline=False)
        elif multiplier == 2:
            embed.add_field(name="Winner!", value=f"💰 Won {formatted_winnings} coins! (2×)", inline=False)
        else:
            embed.add_field(name="No win", value="😢 Better luck next time!", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(aliases=['roll'])
    async def dice(self, ctx, bet: float):
        if bet <= 0:
            return await ctx.send("❌ Bet must be greater than 0!")
        
        user_balance = get_balance(ctx.author.id)
        if user_balance < bet:
            formatted_balance = "{:,.2f}".format(user_balance)
            return await ctx.send(f"❌ You don't have enough Dionysus coins! (Balance: **__{formatted_balance}__**)")
        
        update_balance(ctx.author.id, -bet)
        
        dice1, dice2 = random.randint(1, 6), random.randint(1, 6)
        total = dice1 + dice2
        
        if total == 7:
            multiplier = 3
        elif total in (2, 12):
            multiplier = 4
        elif total <= 4:
            multiplier = 1.5
        else:
            multiplier = 0
        
        winnings = round(bet * multiplier, 2)
        
        if winnings > 0:
            update_balance(ctx.author.id, winnings)
        
        formatted_bet = "{:,.2f}".format(bet)
        formatted_winnings = "{:,.2f}".format(winnings) if winnings > 0 else "0.00"
        
        embed = discord.Embed(
            title="🎲 Dice Game",
            description=f"**Rolled:** {dice1} + {dice2} = **{total}**\n**Bet:** {formatted_bet} Dionysus coins",
            color=0x00ff00 if winnings > 0 else 0xff0000
        )
        
        if winnings > 0:
            embed.add_field(name="Result", value=f"🎉 Won {formatted_winnings} Dionysus coins! ({multiplier}×)", inline=False)
        else:
            embed.add_field(name="Result", value="😢 You lost this round", inline=False)
        
        await ctx.send(embed=embed)
async def setup(bot):
    await bot.add_cog(Gambling(bot))