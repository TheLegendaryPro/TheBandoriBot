# Libs
import discord
from discord.ext import commands
import json
from pathlib import Path
import logging
import datetime
import os
import cogs._json


#--
#-
#




# The place you place your mouse before hitting control shift B
# no longer useful because I started using pyCharm




#
#-
#--

cwd = Path(__file__).parents[0]
cwd = str(cwd)
print(f"{cwd}\n-----")


def get_prefix(bot, message):
    # To read the prefix file and return the prefix for a server
    data = cogs._json.read_json('prefixes')
    if not str(message.guild.id) in data:
        return commands.when_mentioned_or('-')(bot, message)
    return commands.when_mentioned_or(data[str(message.guild.id)])(bot, message)


#Defining a few things
secret_file = json.load(open(cwd+'/bot_config/secrets.json'))
bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True, owner_id=298986102495248386)
bot.config_token = secret_file['token']
logging.basicConfig(level=logging.INFO,
                    filename='bot_data/log.txt',
                    format='%(asctime)s, %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S')


# Read the black list and adins
bot.blacklisted_users = cogs._json.read_json("user_role")["blacklistedUsers"]
bot.bangdream_admins = cogs._json.read_json("user_role")["bangdream_admins"]


bot.cwd = cwd
bot.version = '2.4.5'
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
        data = cogs._json.read_json('prefixes')
        if str(message.guild.id) in data:
            prefix = data[str(message.guild.id)]
        else:
            prefix = '-'
        prefixMsg = await message.channel.send(f"My prefix here is `{prefix}`")

    await bot.process_commands(message)


if __name__ == '__main__':
    # When running this file, if it is the 'main' file
    # I.E its not being imported from another python file run this
    for file in os.listdir(cwd+"/cogs"):
        if file.endswith(".py") and not file.startswith("_"):
            bot.load_extension(f"cogs.{file[:-3]}")
    bot.run(bot.config_token)
