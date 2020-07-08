import discord
from discord.ext import commands
import random



# Game things
map_rows = 6
map_cols = 12

# Initialize the block variables
active_block = True
active_block_row = 3
active_block_col = 0

# Create the game map using a list of lists
def update_map():
    global game_map
    game_map = []
    for row in range(map_rows):
        game_row = []
        for col in range(map_cols):
            game_row.append("")
        game_map.append(game_row)
    if active_block == True:
        game_map[active_block_row][active_block_col] = "1"

def draw_map():
    update_map()
    message = ""
    for row in range(map_rows):
        for col in range(map_cols):
            if game_map[row][col] == "":
                message += ":black_medium_square:"
            else:
                message += "<:idk:565014436104896513>"
        message += "\n"
    return message

update_map()



# Discord things
class Message(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        print("Message Cog has been loaded\n-----")

    @commands.Cog.listener()
    async def on_message(self, message):
        global map_var
        global active_block_row
        global active_block_col
        global active_block
        if message.content == "map":
            await message.delete()
            map_var = await message.channel.send(draw_map())

        if message.content == "update":

            await message.delete()
            await map_var.edit(content = draw_map())

        if message.content == "create":
            active_block = not active_block
            await message.delete()

        if message.content == "w":
            active_block_row -= 1
            if active_block_row < 0:
                active_block_row = map_rows - 1
            await message.delete()
            await map_var.edit(content = draw_map())

        if message.content == "a":
            active_block_col -= 1
            if active_block_col < 0:
                active_block_col = map_cols - 1
            await message.delete()
            await map_var.edit(content = draw_map())

        if message.content == "s":
            active_block_row += 1
            if active_block_row > map_rows - 1:
                active_block_row = 0
            await message.delete()
            await map_var.edit(content = draw_map())

        if message.content == "d":
            active_block_col += 1
            if active_block_col > map_cols - 1:
                active_block_col = 0
            await message.delete()
            await map_var.edit(content = draw_map())

        if message.content == "test":
            await message.channel.send("result")

        if message.content.count('d') == 1 and len(message.content) > 2:
            dice_cont = message.content.replace(" ", "")
            d_pos = dice_cont.find("d")
            dice_count = dice_cont[0:d_pos]
            dice_max = dice_cont[d_pos + 1:]
            try:
                dice_count = int(dice_count)
                dice_max = int(dice_max)
            except ValueError:
                return
            result = ""
            dice_sum = 0
            for i in range(int(dice_count)):
                dice_roll = random.randint(1,dice_max)
                result += "roll {0}:   `{1}`".format(str(i+1), str(dice_roll))
                result += "\n"
                dice_sum += dice_roll
            if int(dice_count) > 1:
                result += "Sum: `{0}`".format(str(dice_sum))
            await message.channel.send(result)

        if message.content == "r":
            dice_roll = random.randint(1,20)
            result = "The result of 1d20:   `{0}`".format(str(dice_roll))
            await message.channel.send(result)



def setup(bot):
    bot.add_cog(Message(bot))
