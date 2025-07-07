from utils.economy_json import get_balance, update_balance
from utils.stocks_prices import get_random_stock_price
from discord.ext import commands
from datetime import datetime
import yfinance as yf
import discord
import random
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
            total_cost = int(parts[1])
        except (ValueError, IndexError):
            return await ctx.send("❌ Invalid format! Use: `!create_company [name] [investment_amount]`")
        except ValueError:
            return await ctx.send("❌ Investment amount must be a whole number!")

        MINIMUM_BALANCE = 5000
        user_balance = get_balance(ctx.author.id)

        if total_cost < MINIMUM_BALANCE:
            return await ctx.send(f"❌ You need to invest at least ${MINIMUM_BALANCE:,} to create a company!")
        if user_balance < total_cost:
            return await ctx.send(f"❌ You don't have enough money for that investment!")
        if total_cost <= 0:
            return await ctx.send("❌ Investment amount must be greater than 0!")
        
        total_shares = int(total_cost / 10)

        owner_shares = int(total_shares * 0.6)
        public_shares = total_shares - owner_shares
        share_price = get_random_stock_price()

        company_data = {
            "name": name,
            "total_shares": total_shares,
            "available_shares": public_shares,
            "share_price": share_price,
            "owner": {
                "id": ctx.author.id,
                "name": str(ctx.author),
                "shares": owner_shares
            },
            "investors": {},
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
        embed.add_field(name="Share Price", value=f"${share_price}", inline=False)
        embed.add_field(name="Total Shares", value=f"`${total_cost:,.2f}`")
        embed.set_footer(text=f"Company created by {ctx.author.display_name}")

        update_balance(ctx.author.id, -total_cost)
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
                embed.add_field(
                    name=f"🏢 {company_name}",
                    value=(
                        f"• **Price:** `${data['share_price']:,.2f}`\n"
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
                f"• **Share Price:** `${company_data['share_price']:,.2f}`"
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
        company_key = None
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
            user_id = str(ctx.author.id)
            is_owner = str(company_data['owner']['id']) == user_id
            
            company_data['available_shares'] -= shares
            
            if is_owner:
                company_data['owner']['shares'] += shares
                transaction_type = "owner shares"
            else:
                investors = company_data['investors']
                investor_key = user_id
                
                if investor_key in investors:
                    investors[investor_key]['shares'] += shares
                else:
                    investors[investor_key] = {
                        'shares': shares,
                        'name': str(ctx.author)
                    }
                transaction_type = "shares"
            
            companies[company_key] = company_data
            self.save_companies(companies)
            
            update_balance(ctx.author.id, -total_cost)
            
            embed = discord.Embed(
                title="✅ Purchase Complete",
                description=f"You bought {shares:,} {transaction_type} of {company_key}",
                color=0x00ff00
            )
            embed.add_field(
                name="Transaction Details",
                value=(
                    f"• **Price per share:** ${company_data['share_price']:,.2f}\n"
                    f"• **Total cost:** ${total_cost:,.2f}\n"
                    f"• **New balance:** ${(user_balance - total_cost):,.2f}\n"
                    f"• **Available shares:** {company_data['available_shares']:,}"
                )
            )
            
            if is_owner:
                embed.add_field(
                    name="Owner Shares",
                    value=f"Total owner shares: {company_data['owner']['shares']:,}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error processing transaction: {e}")
        
    @commands.command()
    async def sell(self, ctx, *, args: str = None):
        if not args:
            return await ctx.send("❌ You must use the format: `!sell {company_name} {stocks}`")
        
        try:
            parts = args.rsplit(' ', 1)
            if len(parts) != 2:
                raise ValueError
            input_name = parts[0]
            shares = int(parts[1])
        except (ValueError, IndexError):
            return await ctx.send("❌ Invalid format! Use: `!sell {company_name} {shares}`")

        if shares <= 0:
            return await ctx.send("❌ You must sell at least 1 share!")
        
        companies = self.load_companies()
        
        company_key = None
        company_data = None
        for name, data in companies.items():
            if name.lower() == input_name.lower():
                company_key = name
                company_data = data
                break
        
        if not company_data:
            return await ctx.send(f"❌ Company '{input_name}' doesn't exist!")
        
        share_price = company_data['share_price']
        user_id = str(ctx.author.id)
        total_shares = company_data['total_shares']
        owner = company_data['owner']

        if share_price <= 0:
            return await ctx.send("❌ This company's shares currently have no value and cannot be sold!")

        if str(owner['id']) == user_id:
            current_owner_shares = owner['shares']
            min_owner_shares = total_shares // 2
            
            max_sellable = current_owner_shares - min_owner_shares
            
            if max_sellable <= 0:
                return await ctx.send("❌ You cannot sell any more shares - you must maintain at least 50% ownership!")
            
            if shares > max_sellable:
                shares = max_sellable
                await ctx.send(f"⚠️ Adjusted sale to {shares} shares to maintain 50% ownership")
            
            total_value = shares * share_price
            
            owner['shares'] -= shares
            company_data['available_shares'] += shares
            
            companies[company_key] = company_data
            self.save_companies(companies)
            
            update_balance(ctx.author.id, total_value)
            
            embed = discord.Embed(
                title="✅ Owner Shares Sold",
                description=f"You sold {shares:,} owner shares of {company_key}",
                color=0x00ff00
            )
            embed.add_field(
                name="Transaction Details",
                value=(
                    f"• **Shares sold:** {shares:,}\n"
                    f"• **Price per share:** ${share_price:,.2f}\n"
                    f"• **Total received:** ${total_value:,.2f}\n"
                    f"• **Remaining owner shares:** {owner['shares']:,} ({owner['shares']/total_shares*100:.1f}%)\n"
                    f"• **Available shares:** {company_data['available_shares']:,}"
                )
            )
            return await ctx.send(embed=embed)
        
        if 'investors' not in company_data or user_id not in company_data['investors']:
            return await ctx.send(f"❌ You don't own any shares in {company_key}!")
        
        investor = company_data['investors'][user_id]
        
        if shares > investor['shares']:
            return await ctx.send(f"❌ You only have {investor['shares']} shares in {company_key}!")
        
        total_value = shares * share_price
        
        investor['shares'] -= shares
        company_data['available_shares'] += shares
        
        if investor['shares'] <= 0:
            del company_data['investors'][user_id]
        
        companies[company_key] = company_data
        self.save_companies(companies)
        
        update_balance(ctx.author.id, total_value)
        
        embed = discord.Embed(
            title="✅ Sale Completed",
            description=f"You sold {shares:,} shares of {company_key}",
            color=0x00ff00
        )
        embed.add_field(
            name="Transaction Details",
            value=(
                f"• **Shares sold:** {shares:,}\n"
                f"• **Price per share:** ${share_price:,.2f}\n"
                f"• **Total received:** ${total_value:,.2f}\n"
                f"• **Remaining shares:** {investor['shares'] if investor['shares'] > 0 else 0:,}"
            )
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=['mycompanies'])
    async def companies(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        companies = self.load_companies()
        user_id = str(target.id)
        
        owned_companies = [
            company['name'] for company in companies.values() 
            if str(company['owner']['id']) == user_id
        ]
        
        if not owned_companies:
            if member:
                return await ctx.send(f"{target.display_name} doesn't own any companies!")
            return await ctx.send("You don't own any companies yet!")
        
        companies_list = "\n".join(f"• {name}" for name in owned_companies)
        embed = discord.Embed(
            title=f"{target.display_name}'s Companies",
            description=companies_list,
            color=0x7289da
        )
        embed.set_footer(text=f"Total companies owned: {len(owned_companies)}")
        
        await ctx.send(embed=embed)

    async def get_random_stock_price():
        stock_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 
            'TSLA', 'NVDA', 'JPM', 'V', 'WMT',
            'DIS', 'NFLX', 'PYPL', 'ADBE', 'INTC'
        ]
        
        random_ticker = random.choice(stock_tickers)
        
        try:
            stock = yf.Ticker(random_ticker)
            
            current_data = stock.history(period='1d')
            
            if not current_data.empty:
                price = current_data['Close'].iloc[-1]
                print(f"Current price of {random_ticker}: ${price:.2f}")
                return price
            else:
                print(f"No data available for {random_ticker}")
                return 1.0
                
        except Exception as e:
            print(f"Error fetching data for {random_ticker}: {str(e)}")
            return 1.0
        
async def setup(bot):
    await bot.add_cog(Stocks(bot))
