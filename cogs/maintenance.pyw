import discord
from discord.ext import commands

class Maintenance(commands.Cog):


    def __init__(self, bot):
        self.bot = bot

    def startmaintenance(self, ctx):
        '''
        Remove messages in bangdream,
        '''



def setup(bot):
    bot.add_cog(QuizGUI(bot))