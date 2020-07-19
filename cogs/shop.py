import discord
from discord.ext import commands
import datetime
import cogs._json

from pathlib import Path


from tinydb import TinyDB, Query
from tinydb.operations import add, set

cwd = Path(__file__).parents[1]
cwd = str(cwd)
db = TinyDB(cwd + '/bot_data/user_db.json', indent=4)


prefix_dict = {
    'TW': 25,
    'EN': 50,
    'JP': 75,
    'Vote what new to add at #suggestions': 9999,
}

del_time = 20 # how long will the message stay before being deleted

async def get_db(ctx):
    doc_id = db.update(add("stars", 0), Query().user_id == ctx.author.id)
    if doc_id == []:
        await ctx.send(f"{ctx.author.name}, we do not have your data, try earning some stars first")
        return
    result = db.search(Query().user_id == ctx.author.id)
    if len(result) > 1:
        await ctx.send(f"{ctx.author.name}, there are problems with the database, contact <@298986102495248386> for help")
        return
    else:
        return result[0]

async def set_db(user_id, attribute, value):
    db.update(set(attribute, value), Query().user_id == user_id)

async def add_db(user_id, attribute = 'stars', amount = 0):
    db.update(add(attribute, amount), Query().user_id == user_id)

class Shop(commands.Cog):


    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shop(self, ctx):
        embed = discord.Embed(title=f'Hi {ctx.author.name}!', description='''Welcome to the shop<:KokoroYes:733655959934861333>, you can buy prefixes and nicknames here''')


        async def get_prefix_text(author):
            text = ''
            # See what the user already have
            data = await get_db(ctx)

            if 'inventory' not in data:
                await set_db(author.id, 'inventory', [])
                data = await get_db(ctx)
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

        embed.add_field(name='Prefixes: ', value=await get_prefix_text(ctx.author))
        await ctx.send(content='Welcome to my shop, grab something', embed=embed, delete_after = del_time)


    @commands.command()
    async def buy(self, ctx, item):
        item = str(item)
        if item in prefix_dict.keys():
            # it is a valid item
            data = await get_db(ctx)
            if 'inventory' not in data:
                # first time
                await set_db(ctx.author.id, 'inventory', [])
                data = await get_db(ctx)
                await ctx.send('seems like this is your first purchase', delete_after = del_time)
            if item not in data['inventory']:
                if data['stars'] < prefix_dict[item]:
                    #don't have enough stars
                    await ctx.send(f"Hey {ctx.author.name}, you don't have enough stars to buy {item}", delete_after = del_time)
                    return
                else:
                    # have enough stars
                    def check(m):
                        # only accept respond from the same guy
                        return ctx.author == m.author

                    try:
                        await ctx.send(f"After purchase, you'll look like **[{item}]{ctx.author.name}**\nType `yes` if you are sure", delete_after = del_time)
                        respond = await self.bot.wait_for('message', check=check, timeout=10)
                    except:
                        await ctx.send(f"Seems like you are not ready, come back when you decided what to buy", delete_after = del_time)
                        return
                    if respond.content.lower() == 'yes':
                        await add_db(ctx.author.id, 'stars', -int(prefix_dict[item]))
                        await set_db(ctx.author.id, 'prefix', item)
                        data = await get_db(ctx)
                        data['inventory'].append(item)
                        await set_db(ctx.author.id, 'inventory', data['inventory'])
                        await ctx.send(f"{ctx.author.name}, the purchase was successful, you now have {data['stars']} stars")
            else:
                await ctx.send(f"Hey {ctx.author.name}, you already have this", delete_after = del_time)
        else:
            await ctx.send(f"{item} is not a valid prefix, you might have typed wrong", delete_after = del_time)

        pass


    @commands.command()
    async def equip(self, ctx, item=None):
        if item == None:
            await set_db(ctx.author.id, "prefix", "")
            await ctx.send(f"{ctx.author.name}, you have removed your prefix")
            return
        item = str(item)
        if item not in prefix_dict.keys():
            await ctx.send(f"Hey {ctx.author.name}, {item} is not a valid item", delete_after = del_time)
        else:
            data = await get_db(ctx)
            if item not in data['inventory']:
                await ctx.send(f"Hey {ctx.author.name}, you don't have {item}", delete_after = del_time)
            else:
                await set_db(ctx.author.id, "prefix", item)
                await ctx.send(f"Success, your prefix has been changed to {item}\nYou can do `-equip` without prefix to remove prefix")


    @commands.command()
    @commands.is_owner()
    async def printdb(self, ctx):
        db.update(add("stars", 0), Query().user_id == ctx.author.id)
        result = db.search(Query().user_id == ctx.author.id)
        await ctx.send(result)


    @commands.command()
    async def leaderboard(self, ctx, me=None):
        if me == None:
            def get_top_ten():
                def get_top_below(results):
                    max = (0, 'name')
                    for item in db:
                        if item['stars'] >= max[0] and 'username' in item:
                            if item['username'] not in [item[1] for item in results]:
                                max = (item['stars'], item['username'])
                    return max

                results = []
                for i in range(10):
                    results.append(get_top_below(results))
                msg = "The Top Ten of Bang Dream Quiz is <:HagumiXD:733655960433721415>:\n"
                for item in results:
                    msg += f"{results.index(item)+1}: {item[1]}     {item[0]}\n"
                return msg

            message = get_top_ten()
            await ctx.send(message)




def setup(bot):
    bot.add_cog(Shop(bot))