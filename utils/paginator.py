import discord
import random

class AnimePaginator(discord.ui.View):
    def __init__(self, anime_list):
        super().__init__(timeout=60)
        self.anime_list = anime_list
        self.index = 0

    def get_embed(self):
        anime = self.anime_list[self.index]
        colors = [
            0x39FF14, 0xFF073A, 0xF5FF00, 0x04D9FF,
            0xBC13FE, 0xFF6EC7, 0xFF9933, 0x7DF9FF
        ]
        embed = discord.Embed(
            title=anime['title'],
            url=anime['anime_url'],
            color=random.choice(colors),
            description=f"**Genres**:\n`{anime['genres']}`\n**Episodes**: `{anime['episodes']}`\n**Description:**\n```\n{anime['synopsis']}\n```"
        )
        if anime['image_url']:
            embed.set_image(url=anime['image_url'])
        embed.set_footer(text=f"{self.index+1} of {len(self.anime_list)}")
        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.red)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index > 0:
            self.index -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            self.index = 4
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.green)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index < len(self.anime_list) - 1:
            self.index += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            self.index = 0
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def on_timeout(self):
        self.clear_items()