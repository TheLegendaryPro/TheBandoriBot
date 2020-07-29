import discord
from discord.ext import commands


class Template(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Commands Cog has been loaded\n-----")

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.channel.DMChannel):
            if message.author.id == 298986102495248386:
                try:
                    await main_dict[552369154594832384].update_log(+ str(message.content))
                except:
                    pass

def setup(bot):
    bot.add_cog(Template(bot))
