import discord
from discord.ext import commands


class Template(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Commands Cog has been loaded\n-----")

def setup(bot):
    bot.add_cog(Template(bot))
