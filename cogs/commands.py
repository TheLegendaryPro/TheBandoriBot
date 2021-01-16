import discord
from discord.ext import commands
import platform

import utils.json

import logging
logger = logging.getLogger(__name__)


class Commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")


    @commands.Cog.listener()
    async def on_ready(self):
        print("Commands Cog has been loaded\n-----")


    @commands.command()
    async def stats(self, ctx):
        """
        A usefull command that displays bot statistics.
        """
        pythonVersion = platform.python_version()
        dpyVersion = discord.__version__
        serverCount = len(self.bot.guilds)
        memberCount = len(set(self.bot.get_all_members()))

        embed = discord.Embed(title=f'{self.bot.user.name} Stats', description='\uFEFF', colour=ctx.author.colour, timestamp=ctx.message.created_at)

        embed.add_field(name='Bot Version:', value=self.bot.version)
        embed.add_field(name='Python Version:', value=pythonVersion)
        embed.add_field(name='Discord.Py Version', value=dpyVersion)
        embed.add_field(name='Total Guilds:', value=serverCount)
        embed.add_field(name='Total Users:', value=memberCount)
        embed.add_field(name='Bot Developers:', value="<@298986102495248386>")

        embed.set_footer(text=f"Carpe Noctem | {self.bot.user.name}")
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)

        await ctx.send(embed=embed)


    @commands.command(aliases=['disconnect', 'close', 'stopbot'])
    @commands.is_owner()
    async def logout(self, ctx):
        """
        If the user running the command owns the bot then this will disconnect the bot from discord.
        """
        await ctx.send(f"Hey {ctx.author.mention}, I am now logging out :wave:")
        await self.bot.logout()


    # @commands.command()
    # async def blacklist(self, ctx, user: discord.Member):
    #     """
    #     Blacklist someone from the bot
    #     """
    #     # Only for those who have permission
    #     if ctx.author.id not in self.bot.bangdream_admins:
    #         return
    #     if user.id == self.bot.owner_id:
    #         await ctx.send("Hey, you cannot blacklist the owner!")
    #         return
    #     if ctx.message.author.id == user.id:
    #         await ctx.send("Hey, you cannot blacklist yourself!")
    #         return
    #
    #     self.bot.blacklisted_users.append(user.id)
    #     data = utils.json.read_json("user_role")
    #     data["blacklistedUsers"].append(user.id)
    #     utils.json.write_json(data, "user_role")
    #     await ctx.send(f"Hey, I have blacklisted {user.name} for you.")
    #
    # @commands.command()
    # async def unblacklist(self, ctx, user: discord.Member):
    #     """
    #     Unblacklist someone from the bot
    #     """
    #     if ctx.author.id not in self.bot.bangdream_admins:
    #         return
    #     self.bot.blacklisted_users.remove(user.id)
    #     data = utils.json.read_json("user_role")
    #     data["blacklistedUsers"].remove(user.id)
    #     utils.json.write_json(data, "user_role")
    #     await ctx.send(f"Hey, I have unblacklisted {user.name} for you.")

    @commands.command()
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def prefix(self, ctx, *, prefix='-'):
        """
        Set a custom prefix for a guild
        """
        guild_data = await self.bot.server_config.find(ctx.guild.id)
        if not guild_data:
            guild_data = {"_id": ctx.guild.id}
        guild_data['prefix'] = prefix
        await self.bot.server_config.upsert(guild_data)
        for item in self.bot.cached_setting:
            if item['_id'] == ctx.guild.id:
                item['prefix'] = prefix
        await ctx.send(f"The guild prefix has been set to `{prefix}`. Use `{prefix}prefix <prefix>` to change it again!")

        # await self.bot.server_config.upsert({"_id": ctx.guild.id, "prefix": prefix})
        # data = utils.json.read_json('prefixes')
        # data[str(ctx.message.guild.id)] = pre
        # utils.json.write_json(data, 'prefixes')
        # await ctx.send(f"The guild prefix has been set to `{pre}`. Use `{pre}prefix <prefix>` to change it again!")




    # @commands.command()
    # @commands.is_owner()
    # async def addadmin(self, ctx, user: discord.Member):
    #     if user.id not in self.bot.bangdream_admins:
    #         self.bot.bangdream_admins.append(user.id)
    #         data = utils.json.read_json("user_role")
    #         data["bangdream_admins"].append(user.id)
    #         utils.json.write_json(data, "user_role")
    #         await ctx.send(f"Hey, {user.name} is now a admin for bangdream")
    #
    # @commands.command()
    # @commands.is_owner()
    # async def removeadmin(self, ctx, user: discord.Member):
    #     if user.id in self.bot.bangdream_admins:
    #         self.bot.bangdream_admins.remove(user.id)
    #         data = utils.json.read_json("user_role")
    #         data["bangdream_admins"].remove(user.id)
    #         utils.json.write_json(data, "user_role")
    #         await ctx.send(f"Hey, {user.name} is no longer a admin for bangdream")


    # @commands.command(aliases=['ZAWARUDO'])
    # async def reloadgame(self, ctx):
    #     """
    #     Reload the game in case it crashes
    #     """
    #     if ctx.author.id not in self.bot.bangdream_admins:
    #         return
    #     await ctx.send("About to reload BanG Dream Quiz, if it is successful, you will see another message")
    #     self.bot.reload_extension("cogs.quizgui")
    #     await ctx.send("You just saw another message, please type -start in bangdream channel to see if it works")


    @commands.command(name="help")
    async def show_help(self, ctx):
        help_content='''\
Start playing by 1.Get inside a voice channel. 2.Press <:RASLogo:727683816755560550>.
Then you can guess the song and band by typing into the chat to earn <:StarGem:727683091337838633>s.
The skip button <:skip:749807101232152606> is for voting to skip and <:StarGem:727683091337838633> is for checking how many star you have.
Then there are a few commands you can use inside #bot-commands:
`-shop`: See what prefixes you can buy
`-stats`: Show the statistics of this bot
`-buy`: Buy a prefix, more details inside shop
`-equip`: Equip a prefix you already own
`-leaderboard`: Show the star leader board of the game
`-help`: Yes, you are here
`-gacha`: Still work in progress gacha function
`-info`: (only in bangdream) DM you info about the song
`-ignore`: (only in bangdream) toggle ignore mode for skip
If you need any help, want to suggest anything or want to praise the bot creator, find <@298986102495248386>
'''
        embed = discord.Embed(title=f"Hi {ctx.author.name}, here is help: ", description=help_content)
        embed.set_footer(text="Join my server at https://discord.gg/wv9SAXn to give comments/suggestions")
        await ctx.send(content='', embed=embed)

    # A function to test if the database is working by adding a point to the owner
    @commands.command()
    @commands.is_owner()
    async def testadd(self, ctx, amount=1):
        if not await self.bot.user_db.increment(ctx.author.id, amount, 'stars'):
            await self.bot.user_db.upsert({
                "_id": ctx.author.id,
                "stars": 1,
                "username": str(ctx.author.name),
                "discriminator": str(ctx.author.discriminator)
            })
        await ctx.send(f"added {amount}")

    # Change to channel that the bot connects to
    @commands.command()
    @commands.check_any(commands.is_owner(), commands.has_permissions(manage_channels=True))
    async def setchannel(self, ctx, v_channel_id=None):
        if not v_channel_id:
            await ctx.send('This command is used to set the voice channel that this bot can connect to:'
                           '\nFor example, `-setchannel 740497127221755924`')
            return
        v_channel_id = int(v_channel_id)
        if self.bot.get_channel(v_channel_id):
            guild_data = await self.bot.server_config.find(ctx.guild.id)
            if not guild_data:
                guild_data = {"_id": ctx.guild.id}
            guild_data['v_channel'] = v_channel_id
            await self.bot.server_config.upsert(guild_data)
            for item in self.bot.cached_setting:
                if item['_id'] == ctx.guild.id:
                    item['v_channel'] = v_channel_id
            await ctx.send(f'The voice channel that I connect to has changed to {str(self.bot.get_channel(v_channel_id))}')



def setup(bot):
    bot.add_cog(Commands(bot))
