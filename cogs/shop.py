import discord
from discord.ext import commands
import random
from pathlib import Path
import asyncio
import logging


# from tinydb import TinyDB, Query
# from tinydb.operations import add, set


# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


cwd = Path(__file__).parents[1]
cwd = str(cwd)
# db = TinyDB(cwd + '/bot_data/user_db.json', indent=4)


prefix_dict = {
    'TW': 25,
    'EN': 50,
    'JP': 75,
    'Dr.': 50,
    'Gt.': 50,
    'Vo.': 50,
    'Key': 50,
    'Ba.': 50,
    'DJ': 50
}

del_time = 20 # how long will the message stay before being deleted

async def get_db(ctx):
    try:
        result = await bot.user_db.find(ctx.author.id)
        if not result:
            await ctx.send(f"{ctx.author.name}, we do not have your data, try earning some stars first")
            return
        else:
            return result
    except Exception as e:
        logger.error(f"Error when get_db for {ctx.author.id}, Error: {e}")
        return
    # doc_id = db.update(add("stars", 0), Query().user_id == ctx.author.id)
    # if doc_id == []:
    #     await ctx.send(f"{ctx.author.name}, we do not have your data, try earning some stars first")
    #     return
    # result = db.search(Query().user_id == ctx.author.id)
    # if len(result) > 1:
    #     await ctx.send(f"{ctx.author.name}, there are problems with the database, contact <@298986102495248386> for help")
    #     return
    # else:
    #     return result[0]

async def set_db(user_id, attribute, value):
    try:
        await bot.user_db.upsert({
            "_id": user_id,
            attribute: value
        })
    except Exception as e:
        logger.error(f"Error when set_db for {user_id}, Error: {e}")
        return
    # db.update(set(attribute, value), Query().user_id == user_id)

async def add_db(user_id, attribute = 'stars', amount = 0):
    # print("add_db", user_id, attribute, amount)
    try:
        await bot.user_db.increment(user_id, amount, attribute)
    except Exception as e:
        logger.error(f"Error when add_db for {user_id}, Error: {e}")
        return
    # db.update(add(attribute, amount), Query().user_id == user_id)

class Shop(commands.Cog):


    def __init__(self, bot):
        self.bot = bot
        self.set_bot()


    def set_bot(self):
        global bot
        bot = self.bot
        logger.info(f'Set bot for {__name__}')

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
        data = await self.bot.user_db.find(ctx.author.id)
        await ctx.send(f"data: {data}")
        # db.update(add("stars", 0), Query().user_id == ctx.author.id)
        # result = db.search(Query().user_id == ctx.author.id)
        # await ctx.send(result)


    @commands.command()
    async def leaderboard(self, ctx, top=None):
        db_result = await bot.user_db.get_all()
        if top != None:
            def get_top_ten():
                def get_top_below(results):
                    max = (0, 'name')
                    for item in db_result:
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
                msg += '\nYou can also do `-leaderboard` to see players around you'
                return msg
            message = get_top_ten()
        else:
            if ctx.author.id in [item["_id"] for item in db_result]:
                result = [item for item in db_result if item["_id"] == ctx.author.id][0]
                self_star = result['stars']

                def search(above, star):
                    closest = (0, 'name')
                    if above:
                        for item in db_result:
                            if item['stars'] > star and item['stars'] - star < abs(closest[0] - star):
                                if 'username' in item:
                                    closest = (item['stars'], item['username'])
                                else:
                                    closest = (item['stars'], 'unknown')
                    else:
                        for item in db_result:
                            if item['stars'] < star and star - item['stars'] < abs(closest[0] - star):
                                if 'username' in item:
                                    closest = (item['stars'], item['username'])
                                else:
                                    closest = (item['stars'], 'unknown')
                    return closest

                result_list = [0,0,0,0,0]
                result_list[2] = (self_star, ctx.author.name)
                result_list[3] = search(False, self_star)
                result_list[4] = search(False, result_list[3][0])
                result_list[1] = search(True, self_star)
                result_list[0] = search(True, result_list[1][0])

                count = 0
                for item in db_result:
                    if item['stars'] > self_star:
                        count += 1

                msg = "You are ranked between\n"
                for item in result_list:
                    msg += f"{result_list.index(item)+1+count-2}: {item[1]}     {item[0]}\n"
                msg += '\nYou can also do `-leaderboard top` to see the top 10 players'
                message = msg

            else:
                message = "You have not played this game yet"
        await ctx.send(message)


    @commands.command()
    @commands.is_owner()
    async def addstars(self, ctx, id, amount):
        if self.bot.get_user(int(id)) != None:
            await add_db(int(id), 'stars', int(amount))
            # db.update(add("stars", int(amount)), Query().user_id == int(id))
            await ctx.send(f"Added {int(amount)} stars to {self.bot.get_user(int(id)).name}")


    @commands.command()
    async def gacha(self, ctx):
        await ctx.send("Sorry, the gacha function is still under development", delete_after=del_time)
        return
        gacha_cost = 0 #todo make it 25
        result = get_db(ctx)
        if not result:
            await ctx.send(f"Hey {ctx.author.name}, you have not played this game yet", delete_after=del_time)
            # If the user doesn't exist
            return
        elif 'stars' not in result:
            await ctx.send(f"Hey {ctx.author.name}, you have not played this game yet", delete_after=del_time)
            #todo exist but don't have stars??
            return
        if result['stars'] < gacha_cost:
            # If the user don't have enough star
            await ctx.send(f"Hey {ctx.author.name}, you don't have enough star to gacha", delete_after=del_time)
            return

        def check(m):
            # only accept respond from the same guy
            return ctx.author == m.author
        try:
            await ctx.send(f"You are about to spend {gacha_cost} <:StarGem:727683091337838633> to do a gacha\nType `yes` if you are sure", delete_after=del_time)
            respond = await self.bot.wait_for('message', check=check, timeout=10)
        except:
            await ctx.send(f"Seems like you are not ready, come back when you decided to gacha", delete_after=del_time)
            return
        if respond.content.lower() != 'yes':
            return
        test_dict = {
    'Dr.': 50,
    'Gt.': 50,
    'Vo.': 50,
    'Key': 50,
    'Ba.': 50,
    'DJ': 50,
}
        pop_list = []
        weight_list = []
        for key, value in test_dict.items():
            pop_list.append(key)
            weight_list.append(300/(value+2))
        roll_results = random.choices(population=pop_list, weights=weight_list, k=6)
        def get_embed(index):
            content_list = ['?']*5
            for n in range(5):
                if n-index+3 <= 5:
                    content_list[n] = roll_results[n-index+3]
                else:
                    content_list[n] = '?'

            content = 'the result is:\n'
            for i in range(len(content_list)):
                if i == 2:
                    content += f'-**{content_list[i]}**-\n'
                else:
                    content += f'{content_list[i]}\n'
            embed = discord.Embed(title='Gacha', description=content)
            embed.set_footer(text="Join my server at https://discord.gg/wv9SAXn to give comments/suggestions")
            return embed
        gacha_msg = await ctx.send(content='.', embed=get_embed(0))
        for i in [1,2,3,4,3]:
            await asyncio.sleep(0.5)
            await gacha_msg.edit(content='.', embed=get_embed(i))
        print(roll_results[2])
        # this is the result
        #todo check if already have it, if no, add it, if yes, return some
        #todo create a message for it




def setup(bot):
    bot.add_cog(Shop(bot))