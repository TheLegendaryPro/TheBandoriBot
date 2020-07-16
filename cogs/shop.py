import discord
from discord.ext import commands
import datetime
import cogs._json

prefix_dict = {
    'TW': 9999,
    'JP': 9999,
    'Beta': 0,
}

def get_user_data():
    # Get and fix user data
    user_data_raw = cogs._json.read_data("user_data")
    user_data = {}
    for i in user_data_raw.keys():
        try:
            user_data[int(i)] = user_data_raw[i]
        except:
            print("failed decode user data raw")
            pass
    return user_data

class Shop(commands.Cog):


    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shop(self, ctx):
        embed = discord.Embed(title=f'Hi {ctx.author.name}!', description='''Welcome to the shop, you can buy prefixes and nicknames here''')


        def get_prefix_text(author):
            text = ''
            # See what the user already have
            data = get_user_data()[author.id]
            if 'inventory' not in data:
                data['inventory'] = []
            for key, value in prefix_dict.items():
                text += f'{key} - '
                if key not in data['inventory']:
                    text += f'{value} <:StarGem:727683091337838633> '
                    text += f'`-buy {key}`'
                else:
                    text += 'obtained'
                    text += f'`-equip {key}`'
                text += '\n'
            return text

        embed.add_field(name='Prefixes: ', value=get_prefix_text(ctx.author))
        await ctx.send(content='shop', embed=embed)


    @commands.command()
    async def buy(self, ctx, item):
        all = get_user_data()
        data = all[ctx.author.id]
        item = str(item)
        if item in prefix_dict.keys():
            # it is a valid item
            if 'inventory' not in data:
                # first time
                data['inventory'] = []
                await ctx.send('seems like this is your first purchase')
            if item not in data['inventory']:
                if data['points'] < prefix_dict[item]:
                    #don't have enough stars
                    await ctx.send(f"Hey {ctx.author.name}, you don't have enough stars to buy {item}")
                    return
                else:
                    # have enough stars
                    def check(m):
                        # only accept respond from the same guy
                        return ctx.message.author == m.author

                    try:
                        await ctx.send(f"After purchase, you'll look like **[{item}]{ctx.author.name}**\nType `yes` if you are sure")
                        respond = await self.bot.wait_for('message', check=check, timeout=10)
                    except:
                        await ctx.send(f"Seems like you are not ready, come back when you decided what to buy")
                        return
                    if respond.content.lower() == 'yes':
                        data['points'] -= prefix_dict[item]
                        data['prefix'] = item
                        data['inventory'].append(item)
                        await ctx.send(f"{ctx.author.name}, the purchase was successful, you now have {data['points']} stars")
                        cogs._json.write_data(all, "user_data")
            else:
                await ctx.send(f"Hey {ctx.author.name}, you already have this")
        else:
            await ctx.send(f"{item} is not a valid prefix, you might have typed wrong")

        pass
        #todo check if item is valid
        #todo check if user have enough stars
        #todo update files to give that thing for the user
        #todo send a confirmation

    @commands.command()
    async def equip(self, ctx, item):
        pass
        #todo check if item is valid
        #todo check if have the item
        #todo update file
        #todo confirmation



def setup(bot):
    bot.add_cog(Shop(bot))