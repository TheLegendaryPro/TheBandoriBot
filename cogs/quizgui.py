import discord
# import pytz
from discord.ext import commands
import asyncio
import utils.json
import random
import jellyfish
import audioread
import logging
import datetime
from pathlib import Path
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


# Set up the current working directory
cwd = Path(__file__).parents[1]
cwd = str(cwd)

# Setup the database
# db = TinyDB(cwd + '/bot_data/user_db.json', indent=4)

# This is the content inside main_dict
main_dict = {
"guild_id": "MusicQuiz object"
}

# Dictionary to change some special characters inside song names
replace_dict = {
    "・": ".",
    "♪": "",
    "☆": "",
    "◎": "",
    "★": "",
    "×": "x"
}

def is_similar(input, answer):
    # to check if the input from user is similar to the song name (answer)
    # Replace special characters
    for key, value in replace_dict.items():
        if key in answer:
            answer = answer.replace(key, value)

    '''check if input is similar to the answer'''
    if jellyfish.jaro_winkler_similarity(input, answer) > 0.88:
        if (abs(len(input)-len(answer)) / max(len(input), len(answer))) < 0.3:
            return True
    return False


all_bands_list = [
    "Poppin'Party",
    "Roselia",
    "RAISE A SUILEN",
    "Morƒonica",
    "Afterglow",
    "Pastel*Palettes",
    "Hello, Happy World!",
    "Glitter*Green",
]


# The quiz object
class MusicQuiz:


    def __init__(self, ctx):
        # Initialize the values inside the object
        self.v_client = None #"voice client object"
        self.song = None #"song object"
        self.display_eng = "?"
        self.display_jp = "?"
        self.display_band = "?"
        self.display_easy = self.display_normal = self.display_hard = self.display_expert = self.display_special = "?"
        self.message = "message object"
        self.t_channel = ctx.channel
        self.v_channel = "voice channel"
        self.log = ["React <:RASLogo:727683816755560550> to start! Type the answer in chat below <:SayoYay:732208214166470677>"]
        self.hint_timer = "timer object"
        self.answer_timer = "timer object"
        self.auto_play = False
        self.next_timer = "timer object"
        self.servers = "all"
        self.skip_vote = []
        self.correct_list = []
        self.guessed_band = []
        self.ignore_list = []


    def get_embed(self):
        """create the embed object and return it"""

        # The description / announcement string for the embed
        embed = discord.Embed(title='Press <:RASLogo:727683816755560550> to start!', description=f'''\
Get help by typing `-help` inside #bot-commands
''')

        embed.add_field(name="Song Name: ", value=f'''{self.display_eng}
{self.display_jp}''')
        embed.add_field(name='Band: ', value=self.display_band)
        # embed.add_field(name="Difficulty", value=f"Expert: {self.display_expert} - Special: {self.display_special}")
        difficulty_value = f'Easy:{self.display_easy} Normal:{self.display_normal} Hard:{self.display_hard} Expert:{self.display_expert} Special:{self.display_special}'
        embed.add_field(name="Difficulty", value=difficulty_value)

        log_msg = ""
        for num in range(len(self.log)):
            if num < len(self.log) - 1:
                log_msg += self.log[num]
            else:
                log_msg += "**" + self.log[num] + "**"
            log_msg += "\n"
        log_msg = log_msg[:-1]
        embed.add_field(inline=False, name='Log: ', value=log_msg)

        embed.set_footer(text = "Join my server at https://discord.gg/wv9SAXn to give comments/suggestions")
        embed.set_author(name = "Made by TheLegendaryPro#6018", icon_url = bot.get_user(bot.owner_id).avatar_url)

        if self.display_eng != "?":
            if self.v_client.is_playing():
                embed.set_thumbnail(url=random.choice(self.song.thumbnails_list))

        return embed


    async def create_message(self):
        """send the message"""
        msg_cont = "Welcome to BanG Dream Music Quiz"
        embed = self.get_embed()
        self.message = await self.t_channel.send(content=msg_cont, embed=embed)
        for item in react_dict.keys():
            await self.message.add_reaction(item)


    async def play_song(self, user):
        """check channel, then client, the play song, set up times"""

        try:
            # See if the user is in a voice channel, if not, return
            voice_channel = user.voice.channel
        except:
            await self.update_log(f"Hey {user.name}, get into voice channel first then click <:RASLogo:727683816755560550> again")
            return

        if not self.v_client:
            # If the voice channel is not defined yet
            if user.voice.channel.guild.id == 432379300684103699:
                # Only redirect people if in official server
                if user.voice.channel.id != 731813919638945802:
                    await self.update_log(f"Hey {user.name}, please go to Music 2 channel then click <:RASLogo:727683816755560550> again")
                    return
            try:
                # Tries to connect
                self.v_client = await voice_channel.connect()
                self.v_channel = voice_channel
            except Exception as e:
                # Cannot connect, maybe it is already connected but something went wrong and it isn't in the music quiz object?
                # Find the voice clients by looping through all voice clients
                for client in bot.voice_clients:
                    # If the client is in this guild
                    if client.guild.id == self.message.channel.guild.id:
                        self.v_client = client
                try:
                    await self.v_client.disconnect()
                except:
                    pass
                self.v_client = await voice_channel.connect()
                self.v_channel = voice_channel

        elif self.v_client.channel != voice_channel:
            # Connected to wrong one, but do not change channel in official server
            if user.voice.channel.guild.id == 432379300684103699:
                if user.voice.channel.id != 731813919638945802:
                    await self.update_log(f"Hey {user.name}, please go to Music 2 channel then click <:RASLogo:727683816755560550> again")
                    return
            await self.v_client.move_to(voice_channel)
            self.v_channel = voice_channel

        # toggle auto play if a song is already playing
        if self.v_client.is_playing():
            await self.toggle_autoplay(user)
            return
        else:
            self.song = Song()

        # Start the player to play a song
        def load_success():
            # This is called when the song is loaded and ready to play
            pass
        try:
            # Some complicated code to play the song then decrease it's volume
            self.v_client.play(discord.FFmpegPCMAudio(f'song_id_files/{self.song.song_id}.ogg'), after=load_success())
            self.v_client.source = discord.PCMVolumeTransformer(self.v_client.source)
            self.v_client.source.volume = 0.14
        except Exception as e:
            await self.update_log('Some error happened, Code: {c}, it says: {m}, hopefully it helps'.format(c = type(e).__name__, m = str(e)))

        # Update the display
        self.display_eng = "?"
        self.display_jp = "?"
        self.display_band = "?"
        self.display_easy = self.display_normal = self.display_hard = self.display_expert = self.display_special = "?"
        # self.display_type = "?"
        self.skip_vote = []
        self.correct_list = []
        self.guessed_band = []
        await self.update_log("<:RASLogo:727683816755560550> Started playing a song")

        # Setup timer for hint
        self.hint_timer = Timer(30, MusicQuiz.give_hint, self)

        # try to cancel next timer
        try:
            self.next_timer.cancel()
        except:
            pass

        # Setup timer for answer and next song
        with audioread.audio_open(f'song_id_files/{self.song.song_name}.ogg') as f:
            self.answer_timer = Timer(int(f.duration) - 30, MusicQuiz.show_answer, self)
            if self.auto_play:
                parameters = (self, user)
                self.next_timer = Timer(int(f.duration) + 15, MusicQuiz.next_song, parameters)


    async def give_hint(self):
        """generate a hint and send it"""
        amount = int(len(self.song.song_name)/1.25) - 1
        hint_list = list("-"*len(self.song.song_name))

        for i in range(amount):
            num = random.randrange(1, len(self.song.song_name))
            hint_list[num] = self.song.song_name[num]
        hint_text = "".join(hint_list)

        # self.display_type = self.song.type
        self.display_easy = self.song.easy
        self.display_normal = self.song.normal
        self.display_hard = self.song.hard
        self.display_expert = self.song.expert
        self.display_special = self.song.special

        await self.update_log(f"<:AyaEh:727684305802756166> Hint: the song name is {hint_text}")
        del self.hint_timer


    async def show_answer(self):
        """show the answer"""
        self.display_eng = self.song.song_name
        self.display_jp = self.song.name_jp
        self.display_band = self.song.band_name
        self.display_easy = self.song.easy
        self.display_normal = self.song.normal
        self.display_hard = self.song.hard
        self.display_expert = self.song.expert
        self.display_special = self.song.special

        # self.display_type = self.song.type
        await self.update_log(f"Time's up, the song was {self.song.song_name}")
        del self.answer_timer


    async def next_song(parameters):
        """the callback for next timer"""
        self, user = parameters
        await self.play_song(user)


    async def skip_song(self, user):
        # See if the voice client is playing anything
        try:
            self.v_client.is_playing()
        except:
            await self.update_log("Cannot skip because no song is playing")
            return
        # Return if the user is not inside the voice channel
        if user.id not in [user.id for user in self.v_channel.members]:
            await self.update_log(f"Hey {user.name}, you are not listening to this song")
            return
        # Return if the user is ignored
        if user.id in self.ignore_list:
            await self.update_log(f"Hey {user.name}, you are in the ignore list therefore cannot vote, type `-ignore` to undo")
            return
        # See if everyone agreed
        if user.id not in self.skip_vote:
            self.skip_vote.append(user.id)
        else:
            pass
        vc_member_list = [user.id for user in self.v_channel.members if (user.id != bot.user.id) and (user.id not in self.ignore_list)]
        if len(self.skip_vote) / len(vc_member_list) > 0.85:
            pass
        else:
            await self.update_log(f"({len(self.skip_vote)}/{len(vc_member_list)}) {user.name} voted to skip, but not everyone agreed")
            return

        # Actually skip the song
        await self.update_log(f"{user.name} skipped {self.song.song_name}, will play another soon")
        self.skip_vote = []
        # Stop all timers
        await self.cancel_all_timers()

        # Stop the song then play the next one in 7 seconds
        self.v_client.stop()
        await asyncio.sleep(7)
        await self.play_song(user)


    async def toggle_autoplay(self, user):
        """toggle and announce autoplay"""
        self.auto_play = not self.auto_play
        await self.update_log(f"auto play is set to {self.auto_play} by {user.name}")


    async def cancel_all_timers(self):
        try:
            self.answer_timer.cancel()
        except:
            pass
        try:
            self.hint_timer.cancel()
        except:
            pass
        try:
            self.next_timer.cancel()
        except:
            pass


    async def check_star(self, user):
        """tell the user how much star he have"""
        try:
            result = await bot.user_db.find(user.id)
            if not result:
                # not result means the result list is empty, then tell the user
                await self.update_log(f"Hey {user.name}, you don't have any <:StarGem:727683091337838633> yet, try answer songs correctly")
            elif 'stars' in result:
                await self.update_log(f"Hi {user.name}, you have {result['stars']} <:StarGem:727683091337838633>, congratulation!")
            else:
                #todo the database contains his name but have no field for stars, let's take it as he has no stars
                # may upsert data, or just add the star field later
                # make here check if username changed as well
                pass
        except Exception as e:
            logger.error(f"Error when check star, user: {user.id}, Error: {e}")

        # try:
        #     # Add 0 stars to the user to refresh the database
        #     db.update(add("stars", 0), Query().user_id == user.id)
        #     result = db.search(Query().user_id == user.id)
        #     if not result:
        #         # not result means the result list is empty, then tell the user
        #         await self.update_log(f"Hey {user.name}, you don't have any <:StarGem:727683091337838633> yet, try answer songs correctly")
        #     elif len(result) == 1:
        #         # Only have one result, which is the way it is supposed to be
        #         star = result[0]['stars']
        #         await self.update_log(f"Hi {user.name}, you have {star} <:StarGem:727683091337838633>, congratulation!")
        #     else:
        #         # Should never have multiple results, raise this error
        #         logger.error(f"{user.id}, have multiple query results, {str(result)}")
        #         await self.update_log(f"The database seems to be broken, please report to @TheLegendaryPro#6018")
        # except:
        #     logger.error(f"query failed! user id is {user.id}")
        #     await self.update_log(f"The database seems to be broken 2, please report to @TheLegendaryPro#6018")
        return


    async def leave_channel(self, user):
        """leave the channel"""
        if not isinstance(self.v_client, str):
            # Disconnet and reset some variables
            await self.v_client.disconnect()
            self.v_client = None
            self.v_channel = "voice channel"
        # Cancel all timers and set it to default value
        await self.cancel_all_timers()


    async def update_log(self, event):
        """Function for processing the log"""
        #todo improve it
        if len(self.log) >= 7:
            del self.log[0]
        need_append = True
        # change last message if stacking
        if self.log[-1].endswith('got it correct too, earning <:StarGem:727683091337838633>'):
            if event.endswith('got it correct too, earning <:StarGem:727683091337838633>'):
                self.log[-1] = self.log[-1][:-57] + 'and ' + event[:-57] + 'got it correct too, earning <:StarGem:727683091337838633>'
                need_append = False
        # another stack
        if self.log[-1].endswith('voted to skip, but not everyone agreed'):
            if event.endswith('voted to skip, but not everyone agreed'):
                self.log[-1] = event[0:6] + self.log[-1][6:-38] + 'and ' + event[6:-38] + 'voted to skip, but not everyone agreed'
                need_append = False
        if need_append:
            self.log.append(event)
        await self.update_message()


    async def update_message(self):
        """Simple function to reload the message"""
        embed = self.get_embed()
        await self.message.edit(embed = embed)


    async def correct_song(self, user):
        """Called when the answer is correct, add the stars"""
        # Append the user to correct list so he can't answer twice
        if user.id not in self.correct_list:
            self.correct_list.append(user.id)
            if self.correct_list.index(user.id) == 0:
                # Check index so no double first hopefully
                await self.add_points(user, 2)
                await self.update_log(f"{user.name} was first to guess the song name, earning <:StarGem:727683091337838633><:StarGem:727683091337838633>")
            else:
                await self.add_points(user, 1)
                await self.update_log(f"{user.name} got it correct too, earning <:StarGem:727683091337838633>")
        else:
            # Don't allow multiple correct answer
            await self.update_log(f"{user.name}, you already answered, why would you answer again?")


    async def correct_band(self, user):
        """Called when the user got the band correct"""
        await self.add_points(user, 1)
        self.display_band = self.song.band_name
        await self.update_log(f"{user.name} got the band right and earned <:StarGem:727683091337838633>")


    async def add_points(self, user, amount):
        """To add points to a user"""
        try:
            if not await bot.user_db.increment(user.id, amount, 'stars'):
                print('not success')
                await bot.user_db.upsert({
                    "_id": user.id,
                    "stars": amount,
                    "username": str(user.name),
                    "discriminator": str(user.discriminator)
                })
        except Exception as e:
            logger.error(f"failed adding {amount} to {user.id}, problem: {e}")
        # try:
        #     result = db.search(Query().user_id == user.id)
        #     if not result:
        #         # result is empty list, first time create data
        #         db.insert({
        #             "user_id": user.id,
        #             "stars": int(amount),
        #             "username": str(user.name),
        #             "discriminator": str(user.discriminator)
        #         })
        #         # Actually adding stars
        #     elif len(result) == 1:
        #         # Add 0 stars to update the database
        #         db.update(add("stars", amount), Query().user_id == user.id)
        #         if "username" not in result[0]:
        #             db.update(set('username', str(user.name)), Query().user_id == user.id)
        #         if "discriminator" not in result[0]:
        #             db.update(set('discriminator', str(user.discriminator)), Query().user_id == user.id)
        #     else:
        #         logger.error(f"failed adding {amount} to {user.id}, too many result")
        # except:
        #     logger.error(f"failed adding {amount} to {user.id}, unable to query or add")

        return


    def __del__(self):
#        print(f"A MusicQuiz object has been destroyed, it is form {ascii(self.v_client.guild.name)}")
        pass





class Song:


    def __init__(self):
        # Reset song_id_data if all songs are played
        if len(song_id_data["not_played"]) == 0:
            while song_id_data['played']:
                song_id_data['not_played'].append(song_id_data['played'].pop())

        # Choose a random song
        popped = song_id_data["not_played"].pop(random.randint(0, len(song_id_data["not_played"]) - 1))
        song_id_data["played"].append(popped)
        details = popped

        # Set up the detials
        self.song_id = details["id"]
        try:
            self.song_name = details["name"]
        except:
            self.song_name = details["title"]
        # Might not have kanji name
        if "kanji" in details:
            self.name_jp = details["kanji"]
        else:
            self.name_jp = "same as english name"
        if "translation" in details:
            self.translation = details["translation"]
        else:
            if "english" in details:
                self.translation = details["english"]
            else:
                self.translation = "no translation"

        self.band_name = details["artist"]

        self.easy = int(details['Easy']['level'])
        self.normal = int(details['Normal']['level'])
        self.hard = int(details['Hard']['level'])
        self.expert = int(details['Expert']['level'])
        # Might not have special
        if "Special" in details:
            self.special = int(details['Special']['level'])
        else:
            self.special = "-"

        self.servers = details['server_list']
        self.lyrics_dict = details['lyric_dict']
        self.thumbnails_list = details['image']


    def __del__(self):
        pass
#        print(f"A Song object is destroyed, the song name is {ascii(self.song_name)}")



# Get song data
# song_id_data = cogs._json.read_data("song_usage_data") #todo

song_id_data_raw = utils.json.read_data("song_id_data")
song_id_data = {
    "not_played": [],
    "played": []
}
for item in song_id_data_raw:
    song_id_data["not_played"].append(item)


class Timer:
    # the parameters may be a tuple
    # Copied it from elsewhere, no idea how it works
    def __init__(self, timeout, callback, parameters):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job(parameters))


    async def _job(self, parameters):
        await asyncio.sleep(self._timeout)
        await self._callback(parameters)
        return


    def cancel(self):
        self._task.cancel()


    def __del__(self):
        pass
#        print(f"A Timer object is destroyed, it's callback is {self._callback}")




async def call_gui(message):
    """When have to initiate the game"""
    global main_dict
    '''when recieve musicgui command'''
    if message.guild.id in main_dict:
        pass
    else:
        # Delete up to 20 message to clear up bangdream text channel
        if message.channel.name == "bangdream":
            await message.channel.purge(limit=20)
        # Create the object and add it to main_dict
        quiz = MusicQuiz(message)
        main_dict[message.guild.id] = quiz
        await quiz.create_message()


async def process_message(message):
    """process the message that was sent in bangdream channel"""
    # return if guild not in main_dict
    if message.guild.id not in main_dict:
        return

    need_check_ans = True
    quiz = main_dict[message.guild.id]

    # return if message not yet created
    if isinstance(quiz.message, str):
        return

    # don't check ans if voice client no playing
    if not quiz.v_client:
        need_check_ans = False

    if need_check_ans:
        if not (quiz.v_client.is_playing()):
            need_check_ans = False

    # see if the answer was answered, if no, check
    if need_check_ans:
        if quiz.display_eng == "?":

            if is_similar(message.content.lower(),quiz.song.song_name.lower()):
                await quiz.correct_song(message.author)
                return
            if is_similar(message.content.lower(),quiz.song.name_jp.lower()) and quiz.song.name_jp != "same as english name":
                await quiz.correct_song(message.author)
                return
            if is_similar(message.content.lower(),quiz.song.translation.lower()) and quiz.song.translation != "no translation":
                await quiz.correct_song(message.author)
                return

        # see if the band name was answered, if no, check
        if quiz.display_band == "?":
            for item in all_bands_list:
                if is_similar(message.content.lower(), item.lower()):
                    if message.author.id in quiz.guessed_band:
                        await quiz.update_log(f"Hey {message.author.name}, you guessed a time already")
                        return
                    quiz.guessed_band.append(message.author.id)
            if is_similar(message.content.lower(),quiz.song.band_name.lower()):
                await quiz.correct_band(message.author)
                return
    # A function within process message
    async def get_name(author):
        # Get the name from the database
        # Add 0 stars to the user to update the database
        try:
            result = await bot.user_db.find(author.id)
            if not result:
                name = author.name
                prefix = ""
            else:
                if 'nickname' in result:
                    name = result['nickname']
                else:
                    name = author.name

                if 'prefix' in result:
                    prefix = result['prefix']
                else:
                    prefix = ""
        except Exception as e:
            logger.error(f"failed to get_name for {author.id}, Error: {e}")
        # db.update(add("stars", 0), Query().user_id == author.id)
        # result = db.search(Query().user_id == author.id)
        # if result == []:
        #     name = author.name
        #     prefix = ""
        # elif len(result) == 1:
        #     if 'nickname' in result[0]:
        #         name = result[0]['nickname']
        #     else:
        #         name = author.name
        #
        #     if 'prefix' in result[0]:
        #         prefix = result[0]['prefix']
        #     else:
        #         prefix = ""
        # else:
        #     name = author.name
        #     prefix = ""
        #     logger.error(f"get name failed, it is {author.name}, too much result {result}")

        if prefix != "":
            prefix = "[" + prefix + "]"
        return f"{prefix}{name}"

    # Get rid of new line
    no_new_line = message.content.replace('\n', '')
    def get_msg(content):
        content = content.replace(':GW', '')
        content = content.replace('**', '')
        return content[:250]

    with open("bot_data/chatlog.txt", "a", encoding="UTF-8") as f:
        f.write(f"\n{datetime.datetime.now()} {str(message.author)}: {no_new_line}")
    await quiz.update_log(f"{await get_name(message.author)}: {get_msg(no_new_line)}")


# The function to deal with reactions and know what to do
react_dict={
"<:RASLogo:727683816755560550>": MusicQuiz.play_song,
"<:skip:749807101232152606>": MusicQuiz.skip_song,
"<:StarGem:727683091337838633>": MusicQuiz.check_star,
}


#todo left off 30/7/2020


# A dict for reaction cooldown
cooldown_dict = {
"key": "random int"
}


async def start_cooldown(key):
    del cooldown_dict[key]


async def process_reaction(reaction, user):

    if reaction.message.id == main_dict[reaction.message.guild.id].message.id:
        if reaction.count > 2:
            await reaction.remove(user)
            return
        try:
            await react_dict[str(reaction.emoji)](main_dict[reaction.message.guild.id], user)
        except KeyError:
            await reaction.remove(user)
        await reaction.remove(user)



class QuizGUI(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.set_bot()


    def set_bot(self):
        global bot
        bot = self.bot
        logger.info(f'Set bot for {__name__}')


    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} Cog has been loaded\n-----")


    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):

        if reaction.message.channel.name == "bangdream":
            if user.id != bot.user.id:
                if user.id in self.bot.blacklisted_users:
                    await reaction.remove(user)
                    return
                await process_reaction(reaction, user)


    @commands.Cog.listener()
    async def on_resumed(self):
        logger.error("on resumed is triggered")
        for key in main_dict.keys():
            if key == "guild_id":
                continue
            try:
                await main_dict[key].message.delete()
            except Exception as e:
                logger.error(f"failed to delete message in {key} because of {type(e).__name__}, {str(e)}")
            try:
                await main_dict[key].create_message()
            except Exception as e:
                logger.error(f"failed to create message in {key} because of {type(e).__name__}, {str(e)}")


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel != None:
            if before.channel.guild.id in main_dict:
                if main_dict[before.channel.guild.id].v_client:
                    if before.channel == main_dict[before.channel.guild.id].v_client.channel:
                        if len(before.channel.members) == 1:
                            await asyncio.sleep(10)
                            if len(before.channel.members) == 1:
                                await main_dict[before.channel.guild.id].leave_channel(member)
                                await main_dict[before.channel.guild.id].update_log("I left the channel because I felt lonely <:RinkoHide:727683091182649457>")




    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.channel.DMChannel):
            if message.author.id == 298986102495248386:
                try:
                    await main_dict[715226997562802227].update_log(str(message.content))
                except:
                    pass
            elif message.author.id == 520283742720491522:
                try:
                    await main_dict[715226997562802227].update_log("TheBandoriBot" + ": " + str(message.content))
                except:
                    pass
            return

        if message.channel.name != "bangdream":
            return

        if message.author.id == self.bot.user.id:
            return

        if message.author.id in self.bot.blacklisted_users:
            await message.delete()
            return

        for word, invoke in command_dict.items():
            if word in message.content.lower():
                if len(message.content) - len(word) < 3:
                    await invoke(message)
                    try:
                        await message.delete()
                    except:
                        pass
                    return

        await process_message(message)
        await message.delete()


async def musicgui(message):
    if message.channel.name == "bangdream":
        await call_gui(message)


async def resend_message(message):
    # todo This is not working
    if message.channel.name == "bangdream":
        # Try if resending the message helps, first delete it
        try:
            for client in bot.voice_clients:
                # If the client is in this guild
                if client.guild.id == message.channel.guild.id:
                    v_client = client
            await v_client.disconnect()
        except:
            pass
        try:
            await main_dict[message.guild.id].message.delete()
            await main_dict[message.guild.id].create_message()
            await message.delete()
        except:
            pass

async def toggle_ignore(message):
    try:
        if message.author.id not in main_dict[message.guild.id].ignore_list:
            main_dict[message.guild.id].ignore_list.append(message.author.id)
            if message.author.id in main_dict[message.guild.id].skip_vote:
                main_dict[message.guild.id].skip_vote.remove(message.author.id)
            await main_dict[message.guild.id].update_log(f"{message.author.name} will now be ignored when voting skip, use `ignore` one more time to undo")
        else:
            main_dict[message.guild.id].ignore_list.remove(message.author.id)
            await main_dict[message.guild.id].update_log(f"{message.author.name} will no longer be ignored when voting skip")
    except:
        pass

async def dm_info(message):
    quiz = main_dict[message.guild.id]
    if not quiz:
        return
    if not quiz.song:
        await message.author.send("There are no songs right now so we cannot get info")
        return

    info_message = f'''**{quiz.song.song_name}**'s info
Server: {quiz.song.servers}
'''
    await message.author.send(info_message)

    for key, value in quiz.song.lyrics_dict.items():
        lyric_message = ''
        lyric_message += f'{key}:\n'
        lyric_message += value
        await message.author.send(lyric_message)


command_dict = {
    "music": musicgui,
    "reloadgame": resend_message,
    "ignore": toggle_ignore,
    "info": dm_info
}


def setup(bot):
    bot.add_cog(QuizGUI(bot))
