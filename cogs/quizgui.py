import discord
import pytz
from discord.ext import commands
import asyncio
import cogs._json
import random
import jellyfish
import audioread
import logging
import datetime
from pathlib import Path
from tinydb import TinyDB, Query
from tinydb.operations import add, set


cwd = Path(__file__).parents[1]
cwd = str(cwd)
db = TinyDB(cwd + '/bot_data/user_db.json', indent=4)


main_dict = {
"guild_id": "MusicQuiz object"
}

replace_dict = {
    "・": ".",
    "♪": "",
    "☆": "",
    "◎": "",
    "★": "",
    "×": "x"
}

def is_similar(input, answer):
    # Replace special characters
    for key, item in replace_dict.items():
        if key in answer:
            answer = answer.replace(key, item)

    '''check if input is similar to the answer'''
    if jellyfish.jaro_winkler_similarity(input, answer) > 0.85:
        if (abs(len(input)-len(answer)) / max(len(input), len(answer))) < 0.3:
            return True
    return False


# The quiz object
class MusicQuiz:


    def __init__(self, ctx):
        self.v_client = "voice client object"
        self.song = "song object"
        self.display_eng = "?"
        self.display_jp = "?"
        self.display_band = "?"
        self.display_expert = "?"
        self.display_special = "?"
        self.display_type = "?"
        self.message = "message object"
        self.t_channel = ctx.channel
        self.v_channel = "voice channel"
        self.log = ["React <:KokoroYay:727683024526770222> to start! Type the answer in chat below <:SayoYay:732208214166470677>"]
        self.hint_timer = "timer object"
        self.answer_timer = "timer object"
        self.auto_play = False
        self.next_timer = "timer object"
        self.servers = "all"
        self.skip_vote = []
        self.correct_list = []


    def get_embed(self):
        '''create the embed object and return it'''
        # If it is maintenance mode, do mot return the normal message
        if not maintenance_mode:
            embed = discord.Embed(title='Press <:KokoroYay:727683024526770222> to start!', description='''Guess the song/band of the playing song and earn <:StarGem:727683091337838633>s!
    Press <:AyaPointUp:727496890693976066>: vote skip, <:StarGem:727683091337838633>: check star
    You can also so `-shop` in bot-commands to buy a prefix''')

            embed.add_field(name="Song Name: ", value=f'''{self.display_eng}
    {self.display_jp}''')
            embed.add_field(name='Band: ', value=self.display_band)
            embed.add_field(name="Difficulty", value=f"Expert: {self.display_expert} - Special: {self.display_special}")

            log_msg = ""
            for num in range(len(self.log)):
                if num < len(self.log) - 1:
                    log_msg += self.log[num]
                else:
                    log_msg += "**" + self.log[num] + "**"
                log_msg += "\n"
            log_msg = log_msg[:-1]
            embed.add_field(inline=False, name='Log: ', value=log_msg)

            # embed.set_footer(text="Below, you can chat, answer song name and answer band name")
            embed.set_footer(text = "Join my server at https://discord.gg/wv9SAXn to give comments/suggestions")
            embed.set_author(name = "Made by TheLegendaryPro#6018", icon_url = bot.get_user(bot.owner_id).avatar_url)

            return embed

        else:
            # Instead return this message
            embed = discord.Embed(title='The bot is under maintenance', description='''The owner of this bot is working on improving the bot
so you cannot use it for now''')

            finish_time = datetime.datetime(2020, 7, 18, 12 - 8, 0, 0, tzinfo=pytz.utc)
            hours, remainder = divmod((finish_time - datetime.datetime.now().astimezone(pytz.utc)).seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            embed.add_field(name="Estimated time until finish: ", value='{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)))

            log_msg = ""
            for num in range(len(self.log)):
                if num < len(self.log) - 1:
                    log_msg += self.log[num]
                else:
                    log_msg += "**" + self.log[num] + "**"
                log_msg += "\n"
            log_msg = log_msg[:-1]
            embed.add_field(inline=False, name='Log: ', value=log_msg)

            # embed.set_footer(text="Below, you can chat, answer song name and answer band name")
            embed.set_footer(text="Join my server at https://discord.gg/wv9SAXn to give comments/suggestions")
            embed.set_author(name="Made by TheLegendaryPro#6018", icon_url=bot.get_user(bot.owner_id).avatar_url)

            return embed


    async def create_message(self):
        '''send the message'''
        msg_cont = "Welcome to BanG Dream Music Quiz"
        embed = self.get_embed()
        self.message = await self.t_channel.send(content=msg_cont, embed=embed)
        for item in react_dict.keys():
            await self.message.add_reaction(item)


    async def play_song(self, user):
        try:
            voice_channel = user.voice.channel
        except:
            # except user is not in a voice channel
            await self.update_log(f"Hey {user.name}, get into voice channel first then click <:KokoroYay:727683024526770222> again")
            return

        if self.v_channel == "voice channel":
            # Only redirect people if in official server
            if user.voice.channel.guild.id == 432379300684103699:
                if user.voice.channel.id != 731813919638945802:
                    await self.update_log(f"Hey {user.name}, please go to Music 2 channel then click <:KokoroYay:727683024526770222> again")
                    return
            try:
                # Tries to connect
                self.v_client = await voice_channel.connect()
                self.v_channel = voice_channel
            except:
                # Try disconnect and reconnect
                try:
                    await self.v_client.disconnect()
                except:
                    self.v_client = self.message.channel.guild.voice_channel
                    await self.v_client.disconnect()
                self.v_client = await voice_channel.connect()
                self.v_channel = voice_channel
        elif self.v_channel != voice_channel:
            # Connected to wrong one, but do not change channel in official server
            if user.voice.channel.guild.id == 432379300684103699:
                if user.voice.channel.id != 731813919638945802:
                    await self.update_log(f"Hey {user.name}, please go to Music 2 channel then click <:KokoroYay:727683024526770222> again")
                    return
            await self.v_client.move_to(voice_channel)
            self.v_channel = voice_channel

        # toggle auto play if a song is already playing
        if self.v_client.is_playing():
            await self.toggle_autoplay(user)
            return
        else:
            self.song = Song(self)

        # Try to save data
        await self.save_data()

        # Start the player to play a song
        def load_success():
            print(f"loaded {ascii(self.song.song_name)}")
        try:
            self.v_client.play(discord.FFmpegPCMAudio(f'song_files/{self.song.song_name}.ogg'), after=load_success())
            self.v_client.source = discord.PCMVolumeTransformer(self.v_client.source)
            self.v_client.source.volume = 0.14
        except Exception as e:
            await self.update_log('Some error happened, Code: {c}, it says: {m}, hopefully it helps'.format(c = type(e).__name__, m = str(e)))

        # Update the display
        self.display_eng = "?"
        self.display_jp = "?"
        self.display_band = "?"
        self.display_expert = "?"
        self.display_special = "?"
        self.display_type = "?"
        self.skip_vote = []
        self.correct_list = []
        await self.update_log("<:RASLogo:727683816755560550> Started playing a song")

        # Setup timer for hint
        self.hint_timer = Timer(20, MusicQuiz.give_hint, self)

        # try to cancel next timer
        try:
            self.next_timer.cancel()
        except:
            pass

        # Setup timer for answer and next song
        with audioread.audio_open(f'song_files/{self.song.song_name}.ogg') as f:
            self.answer_timer = Timer(int(f.duration) - 30, MusicQuiz.show_answer, self)
            if self.auto_play:
                parameters = (self, user)
                self.next_timer = Timer(int(f.duration) + 15, MusicQuiz.next_song, parameters)


    async def give_hint(self):
        '''generate a hint and send it'''
        amount = int(len(self.song.song_name)/1.25) - 1
        hint_list = list("-"*len(self.song.song_name))

        for i in range(amount):
            num = random.randrange(1, len(self.song.song_name))
            hint_list[num] = self.song.song_name[num]
        hint_text = "".join(hint_list)

        self.display_type = self.song.type
        self.display_expert = self.song.expert
        self.display_special = self.song.special

        await self.update_log(f"<:AyaEh:727684305802756166> Hint: the song name is {hint_text}")
        del self.hint_timer


    async def show_answer(self):
        '''show the answer'''
        self.display_eng = self.song.song_name
        self.display_jp = self.song.name_jp
        self.display_band = self.song.band_name
        self.display_expert = self.song.expert
        self.display_special = self.song.special
        self.display_type = self.song.type
        await self.update_log(f"Time's up, the song was {self.song.song_name}")
        del self.answer_timer


    async def next_song(parameters):
        '''the callback for next timer'''
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
            await self.update_log(f"Hey {user.name}, you are not playing")
            return
        # See if everyone agreed
        if user.id not in self.skip_vote:
            self.skip_vote.append(user.id)
        vc_member_list = [user.id for user in self.v_channel.members if user.id != bot.user.id]
        if len(self.skip_vote) / len(vc_member_list) > 0.85:
            pass
        else:
            await self.update_log(f"({len(self.skip_vote)}/{len(vc_member_list)}) {user.name} voted to skip, but not everyone agreed")
            return

        # Actually skip the song
        await self.update_log(f"{user.name} casted the final skip vote, will play another song soon")
        self.skip_vote = []
        # Stop all timers
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
        # Stop the song
        self.v_client.stop()
        await asyncio.sleep(7)
        await self.play_song(user)


    async def toggle_autoplay(self, user):
        '''toggle and announce autoplay'''
        self.auto_play = not self.auto_play
        await self.update_log(f"auto play is set to {self.auto_play} by {user.name}")


    async def check_star(self, user):
        '''tell the user how much star he have'''
        try:
            db.update(add("stars", 0), Query().user_id == user.id)
            result = db.search(Query().user_id == user.id)
            if result == []:
                await self.update_log(f"Hey {user.name}, you don't have any <:StarGem:727683091337838633> yet, try answer songs correctly")
            elif len(result) == 1:
                star = result[0]['stars']
                await self.update_log(f"Hi {user.name}, you have {star} <:StarGem:727683091337838633>, congratulation!")
            else:
                logging.warning(f"{user.id}, have multiple query results, {str(result)}")
                await self.update_log(f"The database seems to be broken, please report to @TheLegendaryPro#6018")
        except:
            logging.warning(f"query failed! user id is {user.id}")
            await self.update_log(f"The database seems to be broken 2, please report to @TheLegendaryPro#6018")

        return


    async def leave_channel(self, user):
        '''leave the channel '''
        if not isinstance(self.v_client, str):
            # Reset some variables
            await self.v_client.disconnect()
            self.v_client = "voice client object"
            self.v_channel = "voice channel"
        try:
            self.hint_timer.cancel()
            self.hint_timer = "timer object"
        except:
            pass
        try:
            self.answer_timer.cancel()
            self.answer_timer = "timer object"
        except:
            pass
        try:
            self.next_timer.cancel()
            self.next_timer = "timer object"
        except:
            pass


    async def save_data(self, user=None):
        if user == None:
            cogs._json.write_data(song_usage_data, "song_usage_data")
            return


    async def update_log(self, event):
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
        embed = self.get_embed()
        await self.message.edit(embed = embed)


    async def correct_song(self, user):
        '''called when the answer is correct, add the stars'''
        if user.id not in self.correct_list:
            self.correct_list.append(user.id)
            if self.correct_list.index(user.id) == 0:
                await self.add_points(user, 2)
                await self.update_log(f"{user.name} was first to guess the song name, earning <:StarGem:727683091337838633><:StarGem:727683091337838633>")
            else:
                await self.add_points(user, 1)
                await self.update_log(f"{user.name} got it correct too, earning <:StarGem:727683091337838633>")
        else:
            await self.update_log(f"{user.name}, you already answered, why would you answer again?")


    async def correct_band(self, user):
        await self.add_points(user, 1)
        self.display_band = self.song.band_name
        await self.update_log(f"{user.name} got the band right and earned <:StarGem:727683091337838633>")


    async def add_points(self, user, amount):
        try:
            result = db.search(Query().user_id == user.id)
            if result == []:
                # first time create data
                db.insert({
                    "user_id": user.id,
                    "stars": int(amount),
                    "username": str(user.name),
                    "discriminator": str(user.discriminator)
                })
            elif len(result) == 1:
                db.update(add("stars", amount), Query().user_id == user.id)
                if "username" not in result[0]:
                    db.update(set('username', str(user.name)), Query().user_id == user.id)
                if "discriminator" not in result[0]:
                    db.update(set('discriminator', str(user.discriminator)), Query().user_id == user.id)

            else:
                logging.warning(f"failed adding {amount} to {user.id}, too many result")
                print(f"failed adding {amount} to {user.id}, too many result")
        except:
            logging.warning(f"failed adding {amount} to {user.id}, unable to query or add")
            print(f"failed adding {amount} to {user.id}, too many result")

        return


    def __del__(self):
#        print(f"A MusicQuiz object has been destroyed, it is form {ascii(self.v_client.guild.name)}")
        pass


server_abbr = {
"jp": "Japanese Server",
"tw": "Taiwanese Server",
"ko": "Korean Server",
"en": "English Server",
"ch": "Chinese Server"
}


class Song:
    def __init__(self, quiz):
        if quiz.servers == "all":
            if len(song_usage_data["not_played"]) == 0:
                for i in list(song_usage_data["played"]):
                    song_usage_data["not_played"][i] = song_usage_data["played"].pop(i)
            choose = random.choice(list(song_usage_data["not_played"].keys()))
            song_usage_data["played"][choose] = song_usage_data["not_played"].pop(choose)
            details = song_usage_data["played"][choose]
        else:
            details = self.getsong(quiz.servers)

        # Set up the detials
        self.song_name = details["song_name"]
        print(f"Song class {ascii(self.song_name)}")
        # Might not have kanji name
        if "kanji" in details:
            self.name_jp = details["kanji"]
        else:
            self.name_jp = "same as english name"
        if "translation" in details:
            self.translation = details["translation"]
        else:
            self.translation = "no translation"
        self.band_name = details["band"]
        self.expert = int(details["Expert"])
        # Might not have special
        if "Special" in details:
            self.special = int(details["Special"])
        else:
            self.special = "No"
        self.type = details["type"]
        if "Server availability" in details:
            self.server_availability = details["Server availability"]


    def getsong(self, servers):
        #[song for song in songs_data_copy["not_played"].keys() if list(set(quiz.servers).intersection(song["Server availability"])) != []]
        # The above is a complicated list comprehention that I decided to not use
        song_data_copy = song_usage_data.copy()
        for song, info in song_data_copy["not_played"].items():
            for server in info["Server availability"]:
                if server in servers:
                    # other than returning song info, also make it played
                    song_usage_data["played"][song] = song_usage_data["not_played"].pop(song)
                    return info

        # No song in not played is in that server
        be_shuffled = list(song_data_copy["played"].values())
        random.shuffle(be_shuffled)
        for info in be_shuffled:
            for server in info["Server availability"]:
                if server in servers:
                    return info


    def __del__(self):
        pass
#        print(f"A Song object is destroyed, the song name is {ascii(self.song_name)}")


# Get song data
song_usage_data = cogs._json.read_data("song_usage_data")


# A timer
class Timer:
    # the parameters may be a tuple
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
    '''process the message that was sent in bangdream channel'''

    # return if guild not in main_dict
    if message.guild.id not in main_dict:
        return

    need_check_ans = True
    quiz = main_dict[message.guild.id]

    # return if message not yet created
    if isinstance(quiz.message, str):
        return

    # don't check ans if voice client no playing
    if isinstance(quiz.v_client, str):
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
            if is_similar(message.content.lower(),quiz.song.band_name.lower()):
                await quiz.correct_band(message.author)
                return


    def get_name(author):


        db.update(add("stars", 0), Query().user_id == author.id)
        result = db.search(Query().user_id == author.id)
        if result == []:
            name = author.name
            prefix = ""
        elif len(result) == 1:
            if 'nickname' in result[0]:
                name = result[0]['nickname']
            else:
                name = author.name

            if 'prefix' in result[0]:
                prefix = result[0]['prefix']
            else:
                prefix = ""
        else:
            name = author.name
            prefix = ""
            logging.warning(f"get name failed, it is {author.name}, too much result {result}")

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
    await quiz.update_log(f"{get_name(message.author)}: {get_msg(no_new_line)}")


# The function to deal with reactions and know what to do
react_dict={
"<:KokoroYay:727683024526770222>": MusicQuiz.play_song,
"<:AyaPointUp:727496890693976066>": MusicQuiz.skip_song,
"<:StarGem:727683091337838633>": MusicQuiz.check_star,
}


# A dict for reaction cooldown
cooldown_dict = {
"key": "random int"
}


async def start_cooldown(key):
    del cooldown_dict[key]


async def process_reaction(reaction, user):
    if maintenance_mode:
        await reaction.remove(user)
        return

    if reaction.message.id == main_dict[reaction.message.guild.id].message.id:
        if reaction.count > 2:
            await reaction.remove(user)
            return
        await react_dict[str(reaction.emoji)](main_dict[reaction.message.guild.id], user)
        await reaction.remove(user)



class QuizGUI(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.set_bot()


    def set_bot(self):
        print("set bot")
        global bot
        bot = self.bot


    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} Cog has been loaded\n-----")


    # @commands.command()
    # async def server(self, ctx, *, abbrs):
    #     ''' Set what game server should the songs come from jp, ko, tw, en, ch'''
    #     if ctx.message.channel.name == "bangdream":
    #         server_list = []
    #         for abbr in server_abbr.keys():
    #             if abbr in abbrs.lower():
    #                 server_list.append(server_abbr[abbr])
    #         if ctx.message.guild.id in main_dict:
    #             if server_list == []:
    #                 main_dict[ctx.message.guild.id].servers = "all"
    #             else:
    #                 main_dict[ctx.message.guild.id].servers = server_list
    #             await main_dict[ctx.message.guild.id].update_log(f"server list: {main_dict[ctx.message.guild.id].servers}")
    #         else:
    #             await ctx.send("You have to do `-mg` to start a game in order to configure its server")


    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.guild.id == 432379300684103699:
            return

        if reaction.message.channel.name == "bangdream":
            if user.id != bot.user.id:
                if user.id in self.bot.blacklisted_users:
                    await reaction.remove(user)
                    return
                await process_reaction(reaction, user)



    @commands.Cog.listener()
    async def on_resumed(self):
        logging.warning("on resumed is triggered")
        for key in main_dict.keys():
            try:
                await main_dict[key].message.delete()
            except Exception as e:
                logging.info(f"failed to delete message in {key} because of {type(e).__name__}, {str(e)}")
            try:
                await main_dict[key].create_message()
            except Exception as e:
                logging.info(f"failed to create message in {key} because of {type(e).__name__}, {str(e)}")


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel != None:
            if before.channel.guild.id in main_dict:
                if not isinstance(main_dict[before.channel.guild.id].v_client, str):
                    if before.channel == main_dict[before.channel.guild.id].v_client.channel and after.channel == None:
                        if len(before.channel.members) == 1:
                            await asyncio.sleep(10)
                            if len(before.channel.members) == 1:
                                await main_dict[before.channel.guild.id].leave_channel(member)
                                await main_dict[before.channel.guild.id].update_log("I left the channel because I felt lonely <:RinkoHide:727683091182649457>")




    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild.id == 432379300684103699:
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
    if message.channel.name == "bangdream":
        # Try if resending the message helps, first delete it
        try:
            main_dict[message.guild.id].v_client.is_playing
        except:
            try:
                await main_dict[message.guild.id].message.delete()
                await main_dict[message.guild.id].create_message()
                await message.delete()
            except:
                pass

maintenance_mode = False

async def startmaintenance(message):
    if message.author.id != bot.owner_id:
        return
    global maintenance_mode
    maintenance_mode = True

async def endmaintenance(message):
    if message.author.id != bot.owner_id:
        return
    global maintenance_mode
    maintenance_mode = False


command_dict = {
"music": musicgui,
"reloadgame": resend_message,
"startmaintenance": startmaintenance,
"endmaintenance": endmaintenance
}


def setup(bot):
    bot.add_cog(QuizGUI(bot))
