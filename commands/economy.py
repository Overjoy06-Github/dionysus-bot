from utils.economy_json import get_balance, update_balance, load_balances
from discord.ext.commands import CommandOnCooldown
from discord.ext import commands
import discord
import random

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx, top: int = 10):
        balances = load_balances()
        sorted_users = sorted(
            balances.items(),
            key=lambda x: x[1]["balance"],
            reverse=True
        )[:top]
        output = "```elixir\n> Top 10 Dionysus Rankings\n\n"
        for rank, (user_id, data) in enumerate(sorted_users, start=1):
            user = await self.bot.fetch_user(int(user_id))
            output = output + f"#{rank}\t@{user.display_name}\n\t\tBalance: {data['balance']} Dionysus Coins\n"
        
        await ctx.send(f"{output}\n```")

    @commands.command(aliases=["bal"])
    async def balance(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        await ctx.send(f"<:dionysus_coin:1391088284825948273> | **{user.display_name}**, you currently have **__{get_balance(user.id):,.2f}__** Dionysus Coins!")

    @balance.error
    async def balance_error(self, ctx, error):
        await ctx.send(f"An error has occurred: {error}", delete_after=3)
        
    @commands.command(aliases=["d"])
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily(self, ctx):
        reward = 500
        update_balance(ctx.author.id, reward)
        await ctx.send(f"🎉 +{reward} coins! Total: {get_balance(ctx.author.id)}")

    @daily.error
    async def daily_error(self, ctx, error):
        if isinstance(error, CommandOnCooldown):
            hours, remainder = divmod(error.retry_after, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            await ctx.send(f"⏳ You've already claimed your daily reward!\nNext claim available in: {int(hours)}h {int(minutes)}m {int(seconds)}s", delete_after=15)
            
    @commands.command(aliases=["pay", "transfer"])
    async def give(self, ctx, member: discord.Member, amount: float):
        amount = round(amount, 2)
        if amount <= 0:
            return await ctx.send("❌ Amount must be positive", delete_after=3)
        if get_balance(ctx.author.id) < amount:
            return await ctx.send("❌ Insufficient funds", delete_after=3)
        
        update_balance(ctx.author.id, -amount)
        update_balance(member.id, amount)
        await ctx.send(f"✅ Gave {member.mention} {amount:,.2f} coins!")

    @give.error
    async def give_error(self, ctx, error):
        await ctx.send(f"An error has occurred: {error}")

    @commands.command(aliases=['slot'])
    async def slots(self, ctx, bet: float = None):
        if not bet:
            return await ctx.send("❌ You must bet an amount! Example: `!slots 50`", delete_after=3)
        
        if bet <= 0:
            return await ctx.send("❌ Bet must be greater than 0!", delete_after=3)
        
        user_balance = get_balance(ctx.author.id)
        if user_balance < bet:
            formatted_balance = "{:,.2f}".format(user_balance)
            return await ctx.send(f"❌ You don't have enough coins! (Balance: {formatted_balance})", delete_after=3)
        
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
    async def dice(self, ctx, bet: float = None):
        if not bet:
            return await ctx.send("❌ You must bet an amount! Example: `!dice 50`", delete_after=3)
        if bet <= 0:
            return await ctx.send("❌ Bet must be greater than 0!", delete_after=3)
        
        user_balance = get_balance(ctx.author.id)
        if user_balance < bet:
            formatted_balance = "{:,.2f}".format(user_balance)
            return await ctx.send(f"❌ You don't have enough Dionysus coins! (Balance: **__{formatted_balance}__**)", delete_after=3)
        
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
    await bot.add_cog(Economy(bot))
