# Libs
import discord
from discord.ext import commands
import json
from pathlib import Path
import logging
import os
import motor.motor_asyncio

import utils.json
from utils.mongo import Document

#--
#-
#


# The place you place your mouse before hitting control shift B
# no longer useful because I started using pyCharm


#
#-
#--

# Get the path
cwd = Path(__file__).parents[0]
cwd = str(cwd)
print(f"{cwd}\n-----")


async def get_prefix(bot, message):
    # Don't have custom prefix for DMs
    if not message.guild:
        return commands.when_mentioned_or("-")

    # # To read the prefix file and return the prefix for a server
    # data = utils.json.read_json('prefixes')
    # if not str(message.guild.id) in data:
    #     return commands.when_mentioned_or('-')(bot, message)
    # return commands.when_mentioned_or(data[str(message.guild.id)])(bot, message)

    try:
        # data = await bot.server_config.find(message.guild.id)
        for item in bot.cached_setting:
            if item['_id'] == message.guild.id:
                data = item

        # Make sure we have a useable prefix
        if not data or "prefix" not in data:
            return commands.when_mentioned_or("-")(bot, message)
        return commands.when_mentioned_or(data["prefix"])(bot, message)
    except:
        return commands.when_mentioned_or("-")(bot, message)


# Defining bot token, database key and owner id
secret_file = json.load(open(cwd+'/bot_config/secrets.json'))
bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True, owner_id=secret_file['owner_id'])
bot.config_token = secret_file['token']
bot.connection_url = secret_file['mongo']


# Set up logging and logger
fh = logging.FileHandler(filename='bot_data/log.txt', encoding='utf-8', mode='a')
fh.setLevel(logging.WARNING)
fh.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt="%Y-%m-%d %H:%M:%S", handlers=[fh, logging.StreamHandler()])
logger = logging.getLogger(__name__)



# Read the black list and adins
bot.blacklisted_users = utils.json.read_json("user_role")["blacklistedUsers"]
bot.bangdream_admins = utils.json.read_json("user_role")["bangdream_admins"]


bot.cwd = cwd
bot.version = '3.1.4'
bot.colors = {
  'WHITE': 0xFFFFFF,
  'AQUA': 0x1ABC9C,
  'GREEN': 0x2ECC71,
  'BLUE': 0x3498DB,
  'PURPLE': 0x9B59B6,
  'LUMINOUS_VIVID_PINK': 0xE91E63,
  'GOLD': 0xF1C40F,
  'ORANGE': 0xE67E22,
  'RED': 0xE74C3C,
  'NAVY': 0x34495E,
  'DARK_AQUA': 0x11806A,
  'DARK_GREEN': 0x1F8B4C,
  'DARK_BLUE': 0x206694,
  'DARK_PURPLE': 0x71368A,
  'DARK_VIVID_PINK': 0xAD1457,
  'DARK_GOLD': 0xC27C0E,
  'DARK_ORANGE': 0xA84300,
  'DARK_RED': 0x992D22,
  'DARK_NAVY': 0x2C3E50
}
bot.color_list = [c for c in bot.colors.values()]


@bot.event
async def on_ready():
    # On ready, print some details to standard out
    print(f"-----\nLogged in as: {bot.user.name} : {bot.user.id}\n-----\nMy current prefix is: -\n-----")
    # This changes the bots 'activity'
    await bot.change_presence(activity=discord.Game(name=f"-help"))

    bot.mongo = motor.motor_asyncio.AsyncIOMotorClient(str(bot.connection_url))
    bot.db = bot.mongo["TheBandoriBot"]
    bot.server_config = Document(bot.db, "server_config")
    await set_up_server_config(bot)
    # todo cache the settings, to minimize data useage
    bot.user_db = Document(bot.db, "user_db")
    print("Initialized Database\n-----")
    logger.warning("the discord bot is ready")


@bot.event
async def on_message(message):
    # Ignore messages sent by yourself
    if message.author.id == bot.user.id:
        return


    # Do not precess message from Direct Message channels
    if isinstance(message.channel, discord.channel.DMChannel):
        return


    # Because of the cog doesn't have attribute problem, will have to set up two listener for on messages
    # So will return if the channel is 'bangdream'
    if message.channel.name == "bangdream":
        return


    #A way to blacklist users from the bot by not processing commands if the author is in the blacklisted_users list
    if message.author.id in bot.blacklisted_users:
        return


    #Whenever the bot is tagged, respond with its prefix
    if f"<@!{bot.user.id}>" in message.content:

        data = await bot.server_config.get_by_id(message.guild.id)
        if not data or "prefix" not in data:
            prefix = "-"
        else:
            prefix = data["prefix"]
        await message.channel.send(f"My prefix here is `{prefix}`", delete_after=15)
    

    #     data = utils.json.read_json('prefixes')
    #     if str(message.guild.id) in data:
    #         prefix = data[str(message.guild.id)]
    #     else:
    #         prefix = '-'
    #     prefixMsg = await message.channel.send(f"My prefix here is `{prefix}`")

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error


async def set_up_server_config(bot):
    bot.cached_setting = await bot.server_config.get_all()

    # Wanted to do monkey-patching to update database cache, too lazy
    # @classmethod
    # async def update_cached_settings(cls, bot):
    #


if __name__ == '__main__':
    # When running this file, if it is the 'main' file
    # I.E its not being imported from another python file run this
    for file in os.listdir(cwd+"/cogs"):
        if file.endswith(".py") and not file.startswith("_"):
            bot.load_extension(f"cogs.{file[:-3]}")
    bot.run(bot.config_token)
