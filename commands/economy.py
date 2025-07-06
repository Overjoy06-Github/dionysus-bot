import discord
from discord.ext import commands
from utils.economy_json import get_balance, update_balance, load_balances
from discord.ext.commands import CommandOnCooldown

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
        await ctx.send(f"An error has occurred: {error}")
        
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
            return await ctx.send("❌ Amount must be positive")
        if get_balance(ctx.author.id) < amount:
            return await ctx.send("❌ Insufficient funds")
        
        update_balance(ctx.author.id, -amount)
        update_balance(member.id, amount)
        await ctx.send(f"✅ Gave {member.mention} {amount:,.2f} coins!")

    @give.error
    async def give_error(self, ctx, error):
        await ctx.send(f"An error has occurred: {error}")

async def setup(bot):
    await bot.add_cog(Economy(bot))