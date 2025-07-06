from discord.ext import commands
from utils.paginator import AnimePaginator
from utils.anime_api import search_anime

class Anime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def anime(self, ctx, *, query):
        try:
            anime_list = search_anime(query)
            if not anime_list:
                return await ctx.send("❌ No anime found with that name.")
            
            view = AnimePaginator(anime_list)
            await ctx.send(embed=view.get_embed(), view=view)
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Anime(bot))