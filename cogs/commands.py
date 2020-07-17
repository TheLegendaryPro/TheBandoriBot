import discord
from discord.ext import commands
import platform

import cogs._json



class Commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


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


    @commands.command()
    async def blacklist(self, ctx, user: discord.Member):
        """
        Blacklist someone from the bot
        """
        # Only for those who have permission
        if ctx.author.id not in self.bot.bangdream_admins:
            return
        if user.id == self.bot.owner_id:
            await ctx.send("Hey, you cannot blacklist the owner!")
            return
        if ctx.message.author.id == user.id:
            await ctx.send("Hey, you cannot blacklist yourself!")
            return

        self.bot.blacklisted_users.append(user.id)
        data = cogs._json.read_json("user_role")
        data["blacklistedUsers"].append(user.id)
        cogs._json.write_json(data, "user_role")
        await ctx.send(f"Hey, I have blacklisted {user.name} for you.")

    @commands.command()
    async def unblacklist(self, ctx, user: discord.Member):
        """
        Unblacklist someone from the bot
        """
        if ctx.author.id not in self.bot.bangdream_admins:
            return
        self.bot.blacklisted_users.remove(user.id)
        data = cogs._json.read_json("user_role")
        data["blacklistedUsers"].remove(user.id)
        cogs._json.write_json(data, "user_role")
        await ctx.send(f"Hey, I have unblacklisted {user.name} for you.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def prefix(self, ctx, *, pre='-'):
        """
        Set a custom prefix for a guild
        """
        data = cogs._json.read_json('prefixes')
        data[str(ctx.message.guild.id)] = pre
        cogs._json.write_json(data, 'prefixes')
        await ctx.send(f"The guild prefix has been set to `{pre}`. Use `{pre}prefix <prefix>` to change it again!")

    @commands.command()
    @commands.is_owner()
    async def addadmin(self, ctx, user: discord.Member):
        if user.id not in self.bot.bangdream_admins:
            self.bot.bangdream_admins.append(user.id)
            data = cogs._json.read_json("user_role")
            data["bangdream_admins"].append(user.id)
            cogs._json.write_json(data, "user_role")
            await ctx.send(f"Hey, {user.name} is now a admin for bangdream")

    @commands.command()
    @commands.is_owner()
    async def removeadmin(self, ctx, user: discord.Member):
        if user.id in self.bot.bangdream_admins:
            self.bot.bangdream_admins.remove(user.id)
            data = cogs._json.read_json("user_role")
            data["bangdream_admins"].remove(user.id)
            cogs._json.write_json(data, "user_role")
            await ctx.send(f"Hey, {user.name} is no longer a admin for bangdream")\


    @commands.command(aliases=['ZAWARUDO'])
    async def reloadgame(self, ctx):
        """
        Reload the game in case it crashes
        """
        if ctx.author.id not in self.bot.bangdream_admins:
            return
        await ctx.send("About to reload BanG Dream Quiz, if it is successful, you will see another message")
        self.bot.reload_extension("cogs.quizgui")
        await ctx.send("You just saw another message, please type -start in bangdream channel to see if it works")





def setup(bot):
    bot.add_cog(Commands(bot))
