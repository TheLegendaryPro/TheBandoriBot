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
event_raw = cogs._json.read_data('event')


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
    if jellyfish.jaro_winkler_similarity(input, answer) > 0.92:
        if (abs(len(input)-len(answer)) / max(len(input), len(answer))) < 0.3:
            return True
    return False


def count_points(team):
    if team == 'red':
        count = 0
        for points in event_raw['red'].values():
            count += points
        return count
    elif team == 'blue':
        count = 0
        for points in event_raw['blue'].values():
            count += points
        return count


def count_player(team):
    if team == 'red':
        count = 0
        for points in event_raw['red'].values():
            count += 1
        return count
    elif team == 'blue':
        count = 0
        for points in event_raw['blue'].values():
            count += 1
        return count


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
        self.result_timer = "timer object"
        self.servers = "all"
        self.correct_list = []
        self.show_result = False


    async def join_red(self, user):
        if str(user.id) not in event_raw["blue"].keys():
            event_raw["red"][str(user.id)] = 0
            await self.update_log(f"{user.name} joined team Red")
        else:
            event_raw["blue"].pop(str(user.id))
            event_raw["red"][str(user.id)] = 0
            await self.update_log(f"{user.name} left team Blue and joined team Red")
        await self.save_data()


    async def join_blue(self, user):
        if str(user.id) not in event_raw["red"].keys():
            event_raw["blue"][str(user.id)] = 0
            await self.update_log(f"{user.name} joined team Blue")
        else:
            event_raw["red"].pop(str(user.id))
            event_raw["blue"][str(user.id)] = 0
            await self.update_log(f"{user.name} left team Red and joined team Blue")
        await self.save_data()


    def get_embed(self):
        '''create the embed object and return it'''
        if not event_started:

            finish_time = datetime.datetime(2020, 7, 19, 21 - 8, 0, 0, tzinfo=pytz.utc)
            hours, remainder = divmod((finish_time - datetime.datetime.now().astimezone(pytz.utc)).seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            embed = discord.Embed(title='upcoming event in 13 UTC, which is in {:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)), description=\
                '''Choose to play for team Red or team Blue, and answer song names with a **92%** accuracy for 10 songs
            The winning team gets to split **400** stars equally between all group mates
            Then the top three players from **each** team will enter into stage 2 and play for 15 songs
            **1st** gets 200 stars and , **2nd** gets 150, **3rd** gets 100, other 3 players get 50 stars
            another round will be hosted for **those that couldn't participate in this one**
            credits to vincent4399#1229 for suggesting this event''')
            embed.add_field(name="Red team: ", value=f"{count_player('red')}")
            embed.add_field(name='Blue Team: ', value=f"{count_player('blue')}")
            log_msg = ""
            for num in range(len(self.log)):
                if num < len(self.log) - 1:
                    log_msg += self.log[num]
                else:
                    log_msg += "**" + self.log[num] + "**"
                log_msg += "\n"
            log_msg = log_msg[:-1]
            embed.add_field(inline=False, name='Log: ', value=log_msg)

            embed.set_footer(text="Join my server at https://discord.gg/wv9SAXn to give comments/suggestions")
            embed.set_author(name="Made by TheLegendaryPro#6018", icon_url=bot.get_user(bot.owner_id).avatar_url)

            return embed

        if not self.show_result:
            embed = discord.Embed(title='Press <:KokoroYay:727683024526770222> to start!', description='''Guess the song/band of the playing song and earn <:Coin:734296760364564571>s!
    Press <:AyaPointUp:727496890693976066>: vote skip, <:Coin:734296760364564571>: check star''')

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

            embed.set_footer(text = "Join my server at https://discord.gg/wv9SAXn to give comments/suggestions")
            embed.set_author(name = "Made by TheLegendaryPro#6018", icon_url = bot.get_user(bot.owner_id).avatar_url)

            return embed
        else:
            embed = discord.Embed(title='Results so far', description='description')

            embed.add_field(name="Red team: ", value=f"{count_points('red')}")
            embed.add_field(name='Blue Team: ', value=f"{count_points('blue')}")

            def get_leaderboard():
                both_team = []
                for key, value in event_raw['red'].items():
                    both_team.append((int(key), value))
                for key, value in event_raw['blue'].items():
                    both_team.append((int(key), value))
                both_team = sorted(both_team, key=lambda x: x[1], reverse=True)
                msg = ""
                for item in both_team[0:6]:
                    msg += f"{both_team.index(item) + 1}: {bot.get_user(item[0]).name} with {item[1]} points\n"
                return msg

            embed.add_field(inline=False, name='Leaderboard: ', value=get_leaderboard())

            log_msg = ""
            for num in range(len(self.log)):
                if num < len(self.log) - 1:
                    log_msg += self.log[num]
                else:
                    log_msg += "**" + self.log[num] + "**"
                log_msg += "\n"
            log_msg = log_msg[:-1]
            embed.add_field(inline=False, name='Log: ', value=log_msg)

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
        self.show_result = False
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
        self.correct_list = []
        await self.update_log("<:RASLogo:727683816755560550> Started playing a song")

        # Setup timer for hint
        self.hint_timer = Timer(30, MusicQuiz.give_hint, self)

        # try to cancel next timer
        try:
            self.result_timer.cancel()
        except:
            pass

        # Setup timer for answer and next song
        with audioread.audio_open(f'song_files/{self.song.song_name}.ogg') as f:

            da_time = int(f.duration) + 5

            self.answer_timer = Timer(int(f.duration) - 30, MusicQuiz.show_answer, self)
            self.result_timer = Timer(da_time, MusicQuiz.show_results, self)



    async def show_results(self):
        self.show_result = True
        await self.update_log("for now, the leaderboard is shown")




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



    async def save_data(self, user=None):
        if user == None:
            cogs._json.write_data(song_usage_data, "song_usage_data")
            cogs._json.write_data(event_raw, "event")
            return


    async def update_log(self, event):
        if len(self.log) >= 7:
            del self.log[0]
        need_append = True
        if need_append:
            self.log.append(event)
        await self.update_message()


    async def update_message(self):
        embed = self.get_embed()
        await self.message.edit(embed = embed)


    async def correct_song(self, user):
        '''called when the answer is correct, add the stars'''
        def check_team(user):
            if str(user.id) in event_raw['red'].keys():
                return 'red'
            elif str(user.id) in event_raw['blue'].keys():
                return 'blue'
            else:
                return None
        team = check_team(user)
        if team == None:
            await self.update_log(f"{user.name}, this contest is only for registered users")
            return

        if user.id not in self.correct_list:
            self.correct_list.append(user.id)
            if self.correct_list.index(user.id) == 0:
                await self.update_log(f"{user.name} got first! team {team} gets <:Coin:734296760364564571><:Coin:734296760364564571><:Coin:734296760364564571><:Coin:734296760364564571><:Coin:734296760364564571>")
                await self.add_points(user, 5, team)
            elif self.correct_list.index(user.id) == 1:
                await self.update_log(f"{user.name} got Second! team {team} gets <:Coin:734296760364564571><:Coin:734296760364564571><:Coin:734296760364564571><:Coin:734296760364564571>")
                await self.add_points(user, 4, team)
            elif self.correct_list.index(user.id) == 2:
                await self.update_log(f"{user.name} got Third! team {team} gets <:Coin:734296760364564571><:Coin:734296760364564571><:Coin:734296760364564571>")
                await self.add_points(user, 3, team)
            elif self.correct_list.index(user.id) == 3:
                await self.update_log(f"{user.name} got Forth! team {team} gets <:Coin:734296760364564571><:Coin:734296760364564571>")
                await self.add_points(user, 2, team)
            elif self.correct_list.index(user.id) >= 4:
                await self.update_log(f"{user.name} got it too! team {team} gets <:Coin:734296760364564571>")
                await self.add_points(user, 1, team)
        else:
            await self.update_log(f"{user.name}, you already answered, why would you answer again?")


    async def correct_band(self, user):
        def check_team(user):
            if str(user.id) in event_raw['red'].keys():
                return 'red'
            elif str(user.id) in event_raw['blue'].keys():
                return 'blue'
            else:
                return None
        team = check_team(user)
        if team == None:
            await self.update_log(f"{user.name}, this contest is only for registered users")
            return

        await self.add_points(user, 2, team)
        self.display_band = self.song.band_name
        await self.update_log(f"{user.name} got the band right and earned <:Coin:734296760364564571><:Coin:734296760364564571>")


    async def add_points(self, user, amount, team):

        try:
            event_raw[team][str(user.id)] += amount
            await self.save_data()
        except Exception as e:
            await self.update_log(f'error in add {amount} points for {user.name}, is {e}')


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



# A dict for reaction cooldown
cooldown_dict = {
"key": "random int"
}

react_dict={
"<:attrPowerful:734211759325446147>": MusicQuiz.join_red,
"<:attrCool:734211759983820811>": MusicQuiz.join_blue,
}


async def start_cooldown(key):
    del cooldown_dict[key]


async def process_reaction(reaction, user):
    if event_started:
        return

    if reaction.message.id == main_dict[reaction.message.guild.id].message.id:
        await react_dict[str(reaction.emoji)](main_dict[reaction.message.guild.id], user)
        await reaction.remove(user)



class EventGUI(commands.Cog):

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


    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.guild.id != 552369154594832384:
            return

        if reaction.message.channel.name == "bangdream":
            if user.id != bot.user.id:
                if event_started:
                    await reaction.remove(user)
                    await reaction.remove(bot.user)
                if user.id in self.bot.blacklisted_users:
                    await reaction.remove(user)
                    return
                await process_reaction(reaction, user)



    # @commands.Cog.listener()
    # async def on_resumed(self):
    #     logging.warning("on resumed is triggered")
    #     for key in main_dict.keys():
    #         try:
    #             await main_dict[key].message.delete()
    #         except Exception as e:
    #             logging.info(f"failed to delete message in {key} because of {type(e).__name__}, {str(e)}")
    #         try:
    #             await main_dict[key].create_message()
    #         except Exception as e:
    #             logging.info(f"failed to create message in {key} because of {type(e).__name__}, {str(e)}")


    # @commands.Cog.listener()
    # async def on_voice_state_update(self, member, before, after):
    #     if before.channel != None:
    #         if before.channel.guild.id in main_dict:
    #             if not isinstance(main_dict[before.channel.guild.id].v_client, str):
    #                 if before.channel == main_dict[before.channel.guild.id].v_client.channel and after.channel == None:
    #                     if len(before.channel.members) == 1:
    #                         await asyncio.sleep(10)
    #                         if len(before.channel.members) == 1:
    #                             await main_dict[before.channel.guild.id].leave_channel(member)
    #                             await main_dict[before.channel.guild.id].update_log("I left the channel because I felt lonely <:RinkoHide:727683091182649457>")




    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild.id != 552369154594832384:
            return

        if message.channel.name != "bangdream":
            return

        if message.author.id == self.bot.user.id:
            return

        if message.author.id in self.bot.blacklisted_users:
            await message.delete()
            return

        if message.author.id == self.bot.owner_id:
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


phase_2 = False
event_started = False

def start_phase_2(message):
    global phase_2
    phase_2 = True

async def play_music(message):
    if message.channel.name == "bangdream":
        try:
            await main_dict[message.guild.id].play_song(message.author)
        except Exception as e:
            await main_dict[message.guild.id].update_log(f"cannot play because {e}")


async def start_event(message):
    global event_started
    event_started = True


command_dict = {
"music": musicgui,
"reloadgame": resend_message,
"startphase2": start_phase_2,
"play": play_music,
"startevent": start_event
}


def setup(bot):
    bot.add_cog(EventGUI(bot))
