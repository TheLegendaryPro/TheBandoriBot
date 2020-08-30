import discord
import pytz
from discord.ext import commands
import asyncio
import utils.json
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
event_raw = utils.json.read_data('event2')


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
    if jellyfish.jaro_winkler_similarity(input, answer) > 0.88:
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
        self.display_difficulty = {
            "easy": "?",
            "normal": "?",
            "hard": "?",
            "expert": "?",
            "special": -1
        }
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
        self.attempt_list = []
        self.event_answer = -1
        self.event_question = "string"
        self.skip_vote = []


    def get_embed(self):
        '''create the embed object and return it'''
        # If it is maintenance mode, do mot return the normal message
        if not event_mode:
            finish_time = datetime.datetime(2020, 7, 29, 20 - 8, 30, 0, tzinfo=pytz.utc)
            td = finish_time - datetime.datetime.now().astimezone(pytz.utc)
            days = td.days
            hours, remainder = divmod(td.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            embed = discord.Embed(title='Press <:KokoroYay:727683024526770222> to start!', description=f'''\
Get help by typing `-help` inside #bot-commands
An event will start in **{days} days,{hours} hours,{minutes} minutes** (29th 12:30 UTC), click <:OtaePing:737164470497050644> to be notified
**In the event**, after the song started playing <:RASLogo:727683816755560550>, The bot will ask questions
Everyone only have **one** chance for **each question**, first to answer correctly gets <:Coin:734296760364564571>
Participants will earn <:StarGem:727683091337838633> if they participate, and more stars if they got into top ten <:SayoYay:732208214166470677>
''')

            embed.add_field(name="Song Name: ", value=f'''{self.display_eng}
{self.display_jp}''')
            embed.add_field(name='Band: ', value=self.display_band)

            diff_msg = ""
            for key, value in self.display_difficulty.items():
                if value == -1:
                    continue
                diff_msg += f"{key}: {value}, "
            diff_msg = diff_msg[:-2]

            embed.add_field(name="Difficulty", value=diff_msg)

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

        if not self.show_result:
            # Event mode
            embed = discord.Embed(title='Event!', description=f'''\
After the song started playing <:RASLogo:727683816755560550>, The bot will ask questions
Let's say the song playing is "Yes BanG Dream"
Bot: What is the expert difficulty of this song
If you enter `20`, you earn <:Coin:734296760364564571> <:KasumiYay2:735009630497013761>, if you enter `19`, you don't
Everyone only have **one** chance for **each question**, first to answer correctly gets <:Coin:734296760364564571>
**Every** event participants gets 25 <:StarGem:727683091337838633>
Then, top ten will get extra <:StarGem:727683091337838633> based on their ranking <:SayoYay:732208214166470677>
''')

#             embed.add_field(name="Song Name: ", value=f'''{self.display_eng}
# {self.display_jp}''')
#             embed.add_field(name='Band: ', value=self.display_band)
#
#             diff_msg = ""
#             for key, value in self.display_difficulty.items():
#                 if value == -1:
#                     continue
#                 diff_msg += f"{key}: {value}, "
#             diff_msg = diff_msg[:-2]
#
#             embed.add_field(name="Difficulty", value=diff_msg)

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

        else:
            embed = discord.Embed(title='Results so far', description='description')

            def get_leaderboard():
                scores = []
                event2_data = utils.json.read_data('event2')
                for key, value in event2_data['event_result'].items():
                    scores.append((int(key), value))
                scores = sorted(scores, key=lambda x: x[1], reverse=True)
                msg = ""
                for item in scores[0:10]:
                    msg += f"{scores.index(item) + 1}: {bot.get_user(item[0]).name} with {item[1]} points\n"
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
                    for client in bot.voice_clients:
                        if client.guild.id == self.message.channel.guild.id:
                            self.v_client = client
                    await self.v_client.disconnect()
                try:
                    self.v_client = await voice_channel.connect()
                except:
                    for client in bot.voice_clients:
                        if client.guild.id == self.message.channel.guild.id:
                            self.v_client = client
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

        if self.v_client.is_playing():
            await self.update_log("I am already playing a song!")
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
        self.display_difficulty = {
            "easy": "?",
            "normal": "?",
            "hard": "?",
            "expert": "?",
            "special": -1
        }
        self.event_question = "string"
        self.skip_vote = []
        try:
            self.song.special
            self.display_difficulty['special'] = "?"
        except:
            pass
        self.display_type = "?"
        self.correct_list = []
        self.attempt_list = []
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

            if not event_mode:
                self.answer_timer = Timer(int(f.duration) - 15, MusicQuiz.show_answer, self)
            if event_mode:
                question_list = ['easy', 'normal', 'hard', 'expert']
                try:
                    int(self.song.special)
                    question_list.append('special')
                except:
                    pass
                random.shuffle(question_list)
                for num in range(1, len(question_list)+1):
                    self.event_question = question_list[num-1]
                    params = (self, question_list[num-1])
                    Timer(int(f.duration * num / 6), MusicQuiz.ask_diff, params)
                self.result_timer = Timer(int(f.duration) + 5, MusicQuiz.trigger_show_result, self)

    async def trigger_show_result(self):
        self.show_result = True
        await self.update_log("results are shown for now")

    async def ask_diff(params):
        self, text = params
        self.attempt_list = []
        self.event_answer = getattr(self.song, text)
        print(self.event_answer)
        await self.update_log(f"<:ConcernedKokori:736552124892184687> What is the {text} difficulty of the song?")


    async def give_hint(self):
        '''generate a hint and send it'''
        amount = int(len(self.song.song_name)/1.25) - 1
        hint_list = list("-"*len(self.song.song_name))

        for i in range(amount):
            num = random.randrange(1, len(self.song.song_name))
            hint_list[num] = self.song.song_name[num]
        hint_text = "".join(hint_list)

        self.display_type = self.song.type

        await self.update_log(f"<:AyaEh:727684305802756166> Hint: the song name is {hint_text}")
        del self.hint_timer


    async def show_answer(self):
        '''show the answer'''
        self.display_eng = self.song.song_name
        self.display_jp = self.song.name_jp
        self.display_band = self.song.band_name
        self.display_difficulty['easy'] = self.song.easy
        self.display_difficulty['normal'] = self.song.normal
        self.display_difficulty['hard'] = self.song.hard
        self.display_difficulty['expert'] = self.song.expert
        try:
            self.display_difficulty['special'] = self.song.special
        except:
            pass
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
        if user.id not in [user.id for user in self.v_chanel.members]:
            await self.update_log(f"Hey {user.name}, you are not playing")
            return
        # See if everyone agreed
        if user.id not in self.skip_vote:
            self.skip_vote.append(user.id)
        else:
            return
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
            utils.json.write_data(song_usage_data, "song_usage_data")
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

    async def add_notify(self, user):
        event2_data = utils.json.read_data('event2')
        if str(user.id) not in event2_data["notify_list"]:
            event2_data["notify_list"].append(str(user.id))
            utils.json.write_data(event2_data, "event2")
            await self.update_log(
                f"Success {user.name}<:AkoYay:733655960094244895>, we will ping you 15 minutes before event begins ({len(event2_data['notify_list'])})")
        else:
            event2_data["notify_list"].remove(str(user.id))
            utils.json.write_data(event2_data, "event2")
            await self.update_log(f"Hey {user.name}, you will no longer be notified")


    async def correct_difficulty(self, user):
        self.event_answer = -1
        data = utils.json.read_data('event2')
        if str(user.id) not in data['event_result'].keys():
            data['event_result'][str(user.id)] = 1
        else:
            data['event_result'][str(user.id)] += 1
        utils.json.write_data(data, 'event2')
        pass



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
        if len(song_usage_data["not_played"]) == 0:
            for i in list(song_usage_data["played"]):
                song_usage_data["not_played"][i] = song_usage_data["played"].pop(i)
        choose = random.choice(list(song_usage_data["not_played"].keys()))
        song_usage_data["played"][choose] = song_usage_data["not_played"].pop(choose)
        details = song_usage_data["played"][choose]

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
        self.easy = int(details["Easy"])
        self.normal = int(details["Normal"])
        self.hard = int(details["Hard"])


    def __del__(self):
        pass
#        print(f"A Song object is destroyed, the song name is {ascii(self.song_name)}")


# Get song data
song_usage_data = utils.json.read_data("song_usage_data")


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
    if need_check_ans and not event_mode:
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

    elif event_mode and need_check_ans:
        try:
            answer_input = int(message.content)
            if message.author.id in quiz.attempt_list:
                return
            if quiz.event_answer == -1:
                return
            quiz.attempt_list.append(message.author.id)
            if answer_input == int(quiz.event_answer):
                await quiz.update_log(f"<:KokoroYes:733655959934861333> {message.author.name} got it correct!, earning <:Coin:734296760364564571>")
                await quiz.correct_difficulty(message.author)
                return
            else:
                return
        except:
            pass




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
"<:OtaePing:737164470497050644>": MusicQuiz.add_notify,
}


# A dict for reaction cooldown
cooldown_dict = {
"key": "random int"
}


async def start_cooldown(key):
    del cooldown_dict[key]


async def process_reaction(reaction, user):
    if event_mode:
        await reaction.remove(user)
        return

    if reaction.message.id == main_dict[reaction.message.guild.id].message.id:
        if reaction.count > 2:
            await reaction.remove(user)
            return
        try:
            await react_dict[str(reaction.emoji)](main_dict[reaction.message.guild.id], user)
        except KeyError:
            await reaction.remove(user)
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
        if reaction.message.guild.id != 432379300684103699:
            return

        if reaction.message.channel.name == "bangdream":
            if user.id != bot.user.id:
                if event_mode:
                    await reaction.remove(user)
                    await reaction.remove(bot.user)
                    return
                if user.id in self.bot.blacklisted_users:
                    await reaction.remove(user)
                    return
                await process_reaction(reaction, user)



    @commands.Cog.listener()
    async def on_resumed(self):
        logging.warning("on resumed is triggered")
        for key in main_dict.keys():
            if key == "guild_id":
                continue
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
                    if before.channel == main_dict[before.channel.guild.id].v_client.channel:
                        if len(before.channel.members) == 1:
                            await asyncio.sleep(10)
                            if len(before.channel.members) == 1:
                                await main_dict[before.channel.guild.id].leave_channel(member)
                                await main_dict[before.channel.guild.id].update_log("I left the channel because I felt lonely <:RinkoHide:727683091182649457>")




    @commands.Cog.listener()
    async def on_message(self, message):

        if message.guild.id != 432379300684103699:
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

event_mode = False

async def play_music(message):
    if message.author.id != bot.owner_id:
        return
    if message.channel.name == "bangdream":
        try:
            await main_dict[message.guild.id].play_song(message.author)
        except Exception as e:
            await main_dict[message.guild.id].update_log(f"cannot play because {e}")


async def startevent(message):
    if message.author.id != bot.owner_id:
        return
    global event_mode
    event_mode = True

async def endevent(message):
    if message.author.id != bot.owner_id:
        return
    global event_mode
    event_mode = False

async def ping_all(message):
    if message.author.id != bot.owner_id:
        return
    event2_data = utils.json.read_data('event2')
    msg = "Hey"
    for id in event2_data['notify_list']:
        msg += f", <@{id}>"
    msg += ". Event is about to start! <:KokoroYes:733655959934861333>"
    await message.channel.send(msg, delete_after = 60)



command_dict = {
"music": musicgui,
"reloadgame": resend_message,
"startevent": startevent,
"endevent": endevent,
"play": play_music,
"ping": ping_all
}


def setup(bot):
    bot.add_cog(EventGUI(bot))
