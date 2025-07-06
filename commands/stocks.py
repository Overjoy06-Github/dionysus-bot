from utils.economy_json import get_balance, update_balance
from discord.ext import commands
from datetime import datetime
import discord
import json

class Stocks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.companies_file = "data/companies.json"

    def load_companies(self):
        with open(self.companies_file, "r") as f:
            return json.load(f)
        
    def save_companies(self, data):
        with open(self.companies_file, "w") as f:
            json.dump(data, f, indent=4)

    @commands.command(aliases=['createcompany', 'newcompany'])
    async def create_company(self, ctx, *, args: str):
        try:
            parts = args.rsplit(' ', 1)
            if len(parts) != 2:
                raise ValueError
            name = parts[0]
            total_shares = int(parts[1])
        except (ValueError, IndexError):
            return await ctx.send("❌ Invalid format! Use: `!create_company [name] [total_shares]`")

        if get_balance(ctx.author.id) < total_shares:
            return await ctx.send("❌ You do not have enough balance to create the company.")
        if total_shares <= 0:
            return await ctx.send("❌ Total shares must be greater than 0!")
        
        owner_shares = int(total_shares * 0.6)
        public_shares = total_shares - owner_shares

        company_data = {
            "name": name,
            "total_shares": total_shares,
            "available_shares": public_shares,
            "share_price": 1.00,
            "owner": {
                "id": ctx.author.id,
                "name": str(ctx.author),
                "shares": owner_shares
            },
            "investors": {},
            "volatility": 0.15,
            "created_at": datetime.utcnow().isoformat()
        }

        companies = self.load_companies()
        if name.lower() in [c.lower() for c in companies.keys()]:
            return await ctx.send("❌ A company with that name already exists!")
        
        companies[name] = company_data
        self.save_companies(companies)

        embed = discord.Embed(
            title=f"🏢 {name} Incorporated!",
            description=f"✅ Successfully created {name} with {total_shares:,} total shares",
            color=0x00ff00
        )
        embed.add_field(name="Owner Shares", value=f"{owner_shares:,} (60%)", inline=True)
        embed.add_field(name="Public Shares", value=f"{public_shares:,} (40%)", inline=True)
        embed.add_field(name="Initial Share Price", value="$1.00", inline=False)
        embed.add_field(name="Cost", value=f"`${total_shares:,}`")
        embed.set_footer(text=f"Company created by {ctx.author.display_name}")

        update_balance(ctx.author.id, -total_shares)
        await ctx.send(embed=embed)

    @commands.command(aliases=['co', 'business', 'corp', 'listcompany'])
    async def company(self, ctx, *, name: str = None):
        companies = self.load_companies()
        if not name:
            if not companies:
                return await ctx.send("ℹ️ There are no companies registered yet!")
            
            embed = discord.Embed(
                title="📊 Available Companies",
                description="Use `!company [name]` to view details",
                color=0x7289da
            )
            
            for company_name, data in companies.items():
                market_cap = data['total_shares'] * data['share_price']
                embed.add_field(
                    name=f"🏢 {company_name}",
                    value=(
                        f"• **Price:** `${data['share_price']:,.2f}`\n"
                        f"• **Market Cap:** `${market_cap:,.2f}`\n"
                        f"• **Available Shares:** `{data['available_shares']:,}/{data['total_shares']:,}`"
                    ),
                    inline=True
                )
            
            await ctx.send(embed=embed)
            return
        
        company_data = None
        for company_name, data in companies.items():
            if company_name.lower() == name.lower():
                company_data = data
                break
        
        if not company_data:
            return await ctx.send(f"❌ No company found with name: {name}")
        
        market_cap = company_data['total_shares'] * company_data['share_price']
        
        embed = discord.Embed(
            title=f"🏢 {company_data['name']} Company Report",
            color=0x7289da
        )
        
        embed.add_field(
            name="📊 Stock Info",
            value=(
                f"• **Total Shares:** {company_data['total_shares']:,}\n"
                f"• **Available Shares:** {company_data['available_shares']:,}\n"
                f"• **Share Price:** `${company_data['share_price']:,.2f}`\n"
                f"• **Market Cap:** `${market_cap:,.2f}`\n"
                f"• **Volatility:** `{company_data['volatility']*100:.0f}%`"
            ),
            inline=False
        )
        
        owner = company_data['owner']
        embed.add_field(
            name="👑 Owner",
            value=(
                f"```elixir\n{owner['name']}```\n"
                f"• **Shares Owned:** {owner['shares']:,}\n"
                f"• **Ownership:** `{owner['shares']/company_data['total_shares']*100:.1f}%`"
            ),
            inline=True
        )
        
        investors = company_data['investors']
        if investors:
            investor_text = "\n".join(
                f"• {data['name']}: {data['shares']:,} shares "
                f"({data['shares']/company_data['total_shares']*100:.1f}%)"
                for user_id, data in investors.items()
            )
        else:
            investor_text = "*No investors yet*"
        
        embed.add_field(
            name="🤝 Investors",
            value=investor_text,
            inline=True
        )
        
        embed.set_footer(text=f"Company created on {company_data['created_at'].split('T')[0]}")
        
        await ctx.send(embed=embed)

    @commands.command()
    async def buy(self, ctx, *, args: str = None):
        if not args:
            return await ctx.send("❌ Usage: `!buy [company name] [shares]`")
        
        try:
            parts = args.rsplit(' ', 1)
            if len(parts) != 2:
                raise ValueError
            company_name = parts[0]
            shares = int(parts[1])
        except (ValueError, IndexError):
            return await ctx.send("❌ Invalid format! Use: `!buy [company name] [shares]`")

        if shares <= 0:
            return await ctx.send("❌ You must buy at least 1 share!")
        
        companies = self.load_companies()
        user_balance = get_balance(ctx.author.id)
        
        company_data = None
        for name, data in companies.items():
            if name.lower() == company_name.lower():
                company_data = data
                company_key = name 
                break
        
        if not company_data:
            return await ctx.send(f"❌ No company found with name: {company_name}")
        
        if company_data['available_shares'] < shares:
            return await ctx.send(
                f"❌ Not enough available shares! "
                f"(Available: {company_data['available_shares']:,})"
            )
        
        total_cost = shares * company_data['share_price']
        
        if user_balance < total_cost:
            return await ctx.send(
                f"❌ Insufficient funds! Need: ${total_cost:,.2f} "
                f"(You have: ${user_balance:,.2f})"
            )
        
        try:
            company_data['available_shares'] -= shares
            
            investors = company_data['investors']
            investor_key = str(ctx.author.id)
            
            if investor_key in investors:
                investors[investor_key]['shares'] += shares
            else:
                investors[investor_key] = {
                    'shares': shares,
                    'name': str(ctx.author)
                }
            
            companies[company_key] = company_data
            self.save_companies(companies)
            
            update_balance(ctx.author.id, -total_cost)
            
            embed = discord.Embed(
                title="✅ Purchase Complete",
                description=f"You bought {shares:,} shares of {company_key}",
                color=0x00ff00
            )
            embed.add_field(
                name="Transaction Details",
                value=(
                    f"• **Price per share:** ${company_data['share_price']:,.2f}\n"
                    f"• **Total cost:** ${total_cost:,.2f}\n"
                    f"• **New balance:** ${(user_balance - total_cost):,.2f}\n"
                    f"• **Remaining shares:** {company_data['available_shares']:,}"
                )
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error processing transaction: {e}")

async def setup(bot):
    await bot.add_cog(Stocks(bot))