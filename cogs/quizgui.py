import json

import discord
from discord.ext import commands
import asyncio
import utils.json
import random
import jellyfish
import audioread
import logging
import datetime
from pathlib import Path
import configparser

setting = configparser.ConfigParser()
setting.read('bot_config/setting.ini')
q_setting = setting['quizgui']

# Set up the logger
logger = logging.getLogger(__name__)

# Set up the current working directory
cwd = Path(__file__).parents[1]
cwd = str(cwd)

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


# To check if the input from user is similar to the song name (answer)
def is_similar(input, answer):
    # Replace special characters
    for key, value in replace_dict.items():
        if key in answer:
            answer = answer.replace(key, value)

    '''check if input is similar to the answer'''
    if jellyfish.jaro_winkler_similarity(input, answer) > 0.88:
        if (abs(len(input) - len(answer)) / max(len(input), len(answer))) < 0.3:
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
        self.v_client = None  # "voice client object"
        self.song = None  # "song object"
        self.display_eng = "?"
        self.display_jp = "?"
        self.display_band = "?"
        self.display_easy = self.display_normal = self.display_hard = self.display_expert = self.display_special = "?"
        self.message = "message object"
        self.t_channel = ctx.channel
        self.v_channel = "voice channel"
        self.log = [('welcome', None)]
        self.display_log = [q_setting['welcome']]
        self.hint_timer = "timer object"
        self.answer_timer = "timer object"
        self.auto_play = False
        self.next_timer = "timer object"
        self.skip_vote = []
        self.correct_list = []
        self.guessed_band = []
        self.ignore_list = []

    def get_embed(self):
        """create the embed object and return it"""

        # The description / announcement string for the embed
        embed = discord.Embed(title='Press <:RASLogo:727683816755560550> to start!', description=f'''\
Get help by typing `-help` inside #bot-commands
<:HagumiXD:733655960433721415> If you like the new feature, else <:NotLikeTsugu:744169674182492171>
''')

        embed.add_field(name="Song Name: ", value=f'{self.display_eng}\n{self.display_jp}')
        embed.add_field(name='Band: ', value=self.display_band)
        difficulty_value = f'Easy:{self.display_easy} Normal:{self.display_normal} Hard:{self.display_hard} ' \
                           f'Expert:{self.display_expert} Special:{self.display_special}'
        embed.add_field(name="Difficulty", value=difficulty_value)

        log_msg = ""
        for num in range(len(self.display_log)):
            if num < len(self.display_log) - 1:
                log_msg += self.display_log[num]
                log_msg += "\n"
            else:
                log_msg += "**" + self.display_log[num] + "**"
        embed.add_field(inline=False, name='Log: ', value=log_msg)

        embed.set_footer(text="Join my server at https://discord.gg/wv9SAXn to give comments/suggestions")
        embed.set_author(name="Made by TheLegendaryPro#6018",
                         icon_url="https://cdn.discordapp.com/avatars/298986102495248386/c36840dfbed5e0e27253ada30eb1dedf.png?size=128")

        # todo make a state variable for this class
        if self.display_eng != "?":
            if self.v_client:
                if self.v_client.is_playing():
                    embed.set_thumbnail(url=random.choice(self.song.thumbnails_list))

        return embed

    async def create_message(self):
        """send the message"""
        msg_cont = "Welcome to BanG Dream Music Quiz"
        embed = self.get_embed()
        self.message = await self.t_channel.send(content=msg_cont, embed=embed)
        for reaction in react_dict.keys():
            await self.message.add_reaction(reaction)

    async def play_song(self, user):
        """check channel, then client, then play song, set up timers"""
        try:
            # See if the user is in a voice channel, if not, return
            voice_channel = user.voice.channel
        except:
            await self.update_log('not_in_channel', user.name)
            logger.exception("not in channel exception")
            return

        if not self.v_client:
            # If the voice channel is not defined yet
            for item in bot.cached_setting:
                if item['_id'] == user.voice.channel.guild.id:
                    if 'v_channel' in item:
                        if user.voice.channel.id != item['v_channel']:
                            await self.update_log('wrong_channel', (user.name, str(bot.get_channel(item['v_channel']))))
                            return

            try:
                # Tries to connect
                self.v_client = await voice_channel.connect()
                self.v_channel = voice_channel
            except:
                # Cannot connect, maybe it is already connected but something went wrong and it isn't in the music quiz object?
                # Find the voice clients by looping through all voice clients
                logger.exception("failed to connect to voice channel at play_song")
                for client in bot.voice_clients:
                    # If the client is in this guild
                    if client.guild.id == self.message.channel.guild.id:
                        self.v_client = client
                try:
                    await self.v_client.disconnect()
                except:
                    logger.exception("failed to disconnect from voice channel at play_song")
                self.v_client = await voice_channel.connect()
                self.v_channel = voice_channel

        elif self.v_client.channel != voice_channel:
            # Connected to wrong one, but do not change channel in official server
            if user.voice.channel.guild.id == 432379300684103699:
                if user.voice.channel.id != 731813919638945802:
                    await self.update_log('wrong_channel', (user.name, 'Music 2'))
                    return
            await self.v_client.move_to(voice_channel)
            self.v_channel = voice_channel

        # toggle auto play if a song is already playing
        if self.v_client.is_playing():
            await self.toggle_autoplay(user)
            return
        else:
            self.song = Song()

        # try to cancel next timer
        try:
            self.next_timer.cancel()
        except:
            pass

        try:
            # Setup timer for answer and next song
            with audioread.audio_open(f'game_ver/{self.song.song_id}.ogg') as f:
                # Set up seek time
                max_seconds = int(f.duration) - 40
                seek_seconds = random.randint(0, max_seconds)
                # Setup timer for hint
                self.hint_timer = Timer(20, MusicQuiz.give_hint, self)
                self.answer_timer = Timer(int(f.duration)-seek_seconds, MusicQuiz.show_answer, self)
                if self.auto_play:
                    parameters = (self, user)
                    self.next_timer = Timer(int(f.duration)-seek_seconds+10, MusicQuiz.next_song, parameters)
        except Exception as e:
            logger.exception("failed to read audio in play_song")
            await self.update_log('chat','Some error happened, Code: {c}, it says: {m}, hopefully it helps'.format(
                                      c=type(e).__name__, m=str(e)))

        # Start the player to play a song
        try:
            # Some complicated code to play the song then decrease it's volume
            self.v_client.play(discord.FFmpegPCMAudio(f'game_ver/{self.song.song_id}.ogg', before_options=f"-ss {seek_seconds}"))
            self.v_client.source = discord.PCMVolumeTransformer(self.v_client.source)
            self.v_client.source.volume = 0.14
        except Exception as e:
            logger.exception("failed to play audio in play_song")
            await self.update_log('chat', 'Some error happened, Code: {c}, it says: {m}, hopefully it helps'.format(
                c=type(e).__name__, m=str(e)))

        # Update the display
        self.display_eng = "?"
        self.display_jp = "?"
        self.display_band = "?"
        self.display_easy = self.display_normal = self.display_hard = self.display_expert = self.display_special = "?"
        self.skip_vote = []
        self.correct_list = []
        self.guessed_band = []
        await self.update_log('start_song')


    async def give_hint(self):
        """generate a hint and send it"""
        amount = int(len(self.song.song_name) / 1.25) - 1
        hint_list = list("-" * len(self.song.song_name))

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

        await self.update_log('hint', hint_text)
        del self.hint_timer

    async def show_answer(self, timeout=True):
        """show the answer"""
        self.display_eng = self.song.song_name
        self.display_jp = self.song.name_jp
        self.display_band = self.song.band_name
        self.display_easy = self.song.easy
        self.display_normal = self.song.normal
        self.display_hard = self.song.hard
        self.display_expert = self.song.expert
        self.display_special = self.song.special

        if timeout:
            await self.update_log('timeout_answer', self.song.song_name)
            del self.answer_timer

    async def next_song(parameters):
        """the callback for next timer"""
        self, user = parameters
        await self.play_song(user)

    async def skip_song(self, user):
        """check for votes, then skip the song"""
        # See if the voice client is playing anything
        try:
            if not self.v_client.is_playing():
                await self.update_log('cannot_skip_no_song_playing')
                return
        except:
            logger.exception("skip_song cannot get voice client")
            await self.update_log('cannot_skip_no_song_playing')
            return
        # Return if the user is not inside the voice channel
        if user.id not in [user.id for user in self.v_channel.members]:
            await self.update_log('cannot_skip_not_in_channel', user.name)
            return
        # Return if the user is ignored
        if user.id in self.ignore_list:
            await self.update_log('cannot_skip_ignored', user.name)
            return
        # See if everyone agreed
        if user.id not in self.skip_vote:
            self.skip_vote.append(user.id)
        else:
            pass
        vc_member_list = [user.id for user in self.v_channel.members if
                          (user.id != bot.user.id) and (user.id not in self.ignore_list)]
        if len(self.skip_vote) / len(vc_member_list) > 0.85:
            pass
        else:
            await self.update_log('vote_skip_not_passed', (user.name, self.skip_vote, len(vc_member_list)))
            return

        # Actually skip the song
        await self.show_answer(timeout=False)
        await self.update_log('success_vote_skip', (user.name, self.song.song_name))
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
        await self.update_log('toggle_autoplay', (user.name, self.auto_play))

    async def cancel_all_timers(self):
        """cancel all timers on a guild"""
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
                await self.update_log('check_star_empty', user.name)
            elif 'stars' in result:
                await self.update_log('check_star', (user.name, result['stars']))
            else:
                await bot.user_db.upsert({'_id': user.id, 'stars': 0})
                # todo make here check if username changed as well
                pass
        except:
            logger.exception(f"Error when check star, user: {user.id}")
        return

    async def like_feature(self, user):
        with open('bot_data/like_dislike.json', 'r') as f:
            like_dislike = json.load(f)
        if user.name not in like_dislike['like']:
            if user.name in like_dislike['dislike']:
                like_dislike['dislike'].remove(user.name)
            like_dislike['like'].append(user.name)
        with open('bot_data/like_dislike.json', 'w') as f:
            json.dump(like_dislike, f, indent=4)
        await self.update_log('chat', f"I am glad that you liked this new feature ({len(like_dislike['like'])})")

    async def dislike_feature(self, user):
        with open('bot_data/like_dislike.json', 'r') as f:
            like_dislike = json.load(f)
        if user.name not in like_dislike['dislike']:
            if user.name in like_dislike['like']:
                like_dislike['like'].remove(user.name)
            like_dislike['dislike'].append(user.name)
        with open('bot_data/like_dislike.json', 'w') as f:
            json.dump(like_dislike, f, indent=4)
        await self.update_log('chat', f"That is unfortunate, you can leave a suggestion in the suggestion section"
                                      f" ({len(like_dislike['dislike'])})")

    async def leave_channel(self, user):
        """leave the voice channel"""
        if not isinstance(self.v_client, str):
            # Disconnet and reset some variables
            await self.v_client.disconnect()
            self.v_client = None
            self.v_channel = "voice channel"
        # Cancel all timers and set it to default value
        await self.cancel_all_timers()

    async def update_log(self, event, parameters=None):
        """Function for processing the log"""

        need_to_append_log = True
        if event == 'chat':
            chat_message = parameters
            self.display_log.append(chat_message)
        elif event == 'welcome':
            self.display_log.append(q_setting['welcome'])
        elif event == 'not_in_channel':
            name = parameters
            self.display_log.append(q_setting['not_in_channel'].format(name=name))
        elif event == 'wrong_channel':
            name, channel_name = parameters
            self.display_log.append(q_setting['wrong_channel'].format(name=name, channel_name=channel_name))
        elif event == 'start_song':
            self.display_log.append(q_setting['start_song'])
        elif event == 'cannot_skip_no_song_playing':
            self.display_log.append(q_setting['cannot_skip_no_song_playing'])
        elif event == 'cannot_skip_not_in_channel':
            name = parameters
            self.display_log.append(q_setting['cannot_skip_not_in_channel'].format(name=name))
        elif event == 'cannot_skip_ignored':
            name = parameters
            self.display_log.append(q_setting['cannot_skip_ignored'].format(name=name))
        elif event == 'vote_skip_not_passed':
            name, for_users, user_count = parameters
            if not self.log[-1][0] == 'vote_skip_not_passed':
                self.display_log.append(q_setting['vote_skip_not_passed'].format(
                    name=name, for_count=len(for_users), user_count=user_count
                ))
            else:
                need_to_append_log = False
                self.display_log[-1] = q_setting['vote_skip_not_passed'].format(
                    name=', '.join([bot.get_user(id).name for id in for_users]), for_count=len(for_users),
                    user_count=user_count
                )
        elif event == 'success_vote_skip':
            name, song_name = parameters
            self.display_log.append(q_setting['success_vote_skip'].format(
                name=name, song_name=song_name
            ))
        elif event == 'toggle_autoplay':
            name, value = parameters
            self.display_log.append(q_setting['toggle_autoplay'].format(name=name, value=value))
        elif event == 'check_star_empty':
            name = parameters
            self.display_log.append(q_setting['check_star_empty'].format(name=name))
        elif event == 'check_star':
            name, value = parameters
            self.display_log.append(q_setting['check_star'].format(name=name, value=value))
        elif event == 'correct_song_first':
            name = parameters
            self.display_log.append(q_setting['correct_song_first'].format(name=name))
        elif event == 'correct_song_also':
            name_list = parameters
            if not self.log[-1][0] == 'correct_song_also':
                self.display_log.append(q_setting['correct_song_also'].format(name=bot.get_user(name_list[-1]).name))
            else:
                need_to_append_log = False
                self.display_log[-1] = q_setting['correct_song_also'].format(
                    name=', '.join([bot.get_user(id).name for id in name_list]))
        elif event == 'correct_song_again':
            name = parameters
            if not self.log[-1][0] == 'correct_song_again':
                self.display_log.append(q_setting['correct_song_again'].format(name=name))
            else:
                need_to_append_log = False
                self.display_log[-1] = q_setting['correct_song_again'].format(name=name)
        elif event == 'correct_band':
            name = parameters
            self.display_log.append(q_setting['correct_band'].format(name=name))
        elif event == 'hint':
            hint = parameters
            self.display_log.append(q_setting['hint'].format(hint=hint))
        elif event == 'timeout_answer':
            answer = parameters
            self.display_log.append(q_setting['timeout_answer'].format(answer=answer))
        elif event == 'answer_band_again':
            name = parameters
            if not self.log[-1][0] == 'answer_band_again':
                self.display_log.append(q_setting['answer_band_again'].format(name=name))
            else:
                need_to_append_log = False
                self.display_log[-1] = q_setting['answer_band_again'].format(name=name)
        elif event == 'ignore_on':
            name = parameters
            self.display_log.append(q_setting['ignore_on'].format(name=name))
        elif event == 'ignore_off':
            name = parameters
            self.display_log.append(q_setting['ignore_off'].format(name=name))
        elif event == 'leave_channel':
            self.display_log.append(q_setting['leave_channel'])

        if need_to_append_log:
            self.log.append((event, parameters))
        else:
            self.log[-1] = (event, parameters)

        if len(self.display_log) > 7:
            self.display_log.pop(0)
            self.log.pop(0)

        await self.update_message()

    async def update_message(self):
        """Simple function to reload the message"""
        embed = self.get_embed()
        await self.message.edit(embed=embed)

    async def correct_song(self, user):
        """Called when the answer is correct, add the stars"""
        # Append the user to correct list so he can't answer twice
        if user.id not in self.correct_list:
            self.correct_list.append(user.id)
            if self.correct_list.index(user.id) == 0:
                # Check index so no double first hopefully
                await self.add_points(user, 2)
                await self.update_log('correct_song_first', user.name)
            else:
                await self.add_points(user, 1)
                await self.update_log('correct_song_also', self.correct_list[1:])
        else:
            # Don't allow multiple correct answer
            await self.update_log('correct_song_again', user.name)

    async def correct_band(self, user):
        """Called when the user got the band correct"""
        await self.add_points(user, 1)
        self.display_band = self.song.band_name
        await self.update_log('correct_band', user.name)

    async def add_points(self, user, amount):
        """To add points to a user"""
        try:
            if not await bot.user_db.increment(user.id, amount, 'stars'):
                await bot.user_db.upsert({
                    "_id": user.id,
                    "stars": amount,
                    "username": str(user.name),
                    "discriminator": str(user.discriminator)
                })
        except:
            logger.exception(f"failed adding {amount} to {user.id}")
        return


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
        if "english" in details:
            self.translation = details["english"]
        else:
            if "translation" in details:
                self.translation = details["translation"]
            else:
                self.translation = "no translation"

        if isinstance(details["artist"], str):
            self.band_name = details["artist"]
        else:
            self.band_name = "".join(details["artist"])
        self.easy = int(details['Easy']['level'])
        self.normal = int(details['Normal']['level'])
        self.hard = int(details['Hard']['level'])
        self.expert = int(details['Expert']['level'])
        # Might not have special
        if "Special" in details:
            self.special = int(details['Special']['level'])
        else:
            self.special = "-"

        self.lyrics_dict = details['lyric_dict']
        self.thumbnails_list = details['song_images']


# Get song data
song_id_data_raw = utils.json.read_data("new_id_data")
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


async def call_gui(message):
    """When have to initiate the game"""
    global main_dict
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

            if is_similar(message.content.lower(), quiz.song.song_name.lower()):
                await quiz.correct_song(message.author)
                return
            if is_similar(message.content.lower(),
                          quiz.song.name_jp.lower()) and quiz.song.name_jp != "same as english name":
                await quiz.correct_song(message.author)
                return
            if is_similar(message.content.lower(),
                          quiz.song.translation.lower()) and quiz.song.translation != "no translation":
                await quiz.correct_song(message.author)
                return

        # see if the band name was answered, if no, check
        if quiz.display_band == "?":
            for item in all_bands_list:
                if is_similar(message.content.lower(), item.lower()):
                    if message.author.id in quiz.guessed_band:
                        await quiz.update_log('answer_band_again', message.author.name)
                        return
                    quiz.guessed_band.append(message.author.id)
            if is_similar(message.content.lower(), quiz.song.band_name.lower()):
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
    await quiz.update_log('chat', f"{await get_name(message.author)}: {get_msg(no_new_line)}")


# The function to deal with reactions and know what to do
react_dict = {
    "<:RASLogo:727683816755560550>": MusicQuiz.play_song,
    "<:AyaPointUp:727496890693976066>": MusicQuiz.skip_song,
    "<:StarGem:727683091337838633>": MusicQuiz.check_star,
    "<:HagumiXD:733655960433721415>": MusicQuiz.like_feature,
    "<:NotLikeTsugu:744169674182492171>": MusicQuiz.dislike_feature,
}


async def process_reaction(reaction, user):
    """react to reactions"""
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
        await initiate_message()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """check if have to react, then call process_reaction"""
        if reaction.message.channel.name == "bangdream":
            if user.id != bot.user.id:
                if user.id in self.bot.blacklisted_users:
                    await reaction.remove(user)
                    return
                await process_reaction(reaction, user)

    @commands.Cog.listener()
    async def on_resumed(self):
        """apparently things break when discord resumes, so we restart when it resumes"""
        logger.error("on resumed is triggered")
        for key in main_dict.keys():
            if key == "guild_id":
                continue
            try:
                await main_dict[key].message.delete()
            except:
                logger.exception(f"failed to delete message in {key}")
            try:
                await main_dict[key].create_message()
            except:
                logger.exception(f"failed to create message in {key}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """check if need to leave whenever someone leave or join"""
        if before.channel != None:
            if before.channel.guild.id in main_dict:
                if main_dict[before.channel.guild.id].v_client:
                    if before.channel == main_dict[before.channel.guild.id].v_client.channel:
                        if len(before.channel.members) == 1:
                            await asyncio.sleep(10)
                            if len(before.channel.members) == 1:
                                await main_dict[before.channel.guild.id].leave_channel(member)
                                await main_dict[before.channel.guild.id].update_log("leave_channel")

    @commands.Cog.listener()
    async def on_message(self, message):
        """check if we have to process the message, then process it"""
        if isinstance(message.channel, discord.channel.DMChannel):
            if message.author.id == 298986102495248386:
                try:
                    await main_dict[715226997562802227].update_log('chat', str(message.content))
                except:
                    pass
            elif message.author.id == 520283742720491522:
                try:
                    await main_dict[715226997562802227].update_log('chat',
                                                                   "TheBandoriBot" + ": " + str(message.content))
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


async def toggle_ignore(message):
    try:
        if message.author.id not in main_dict[message.guild.id].ignore_list:
            main_dict[message.guild.id].ignore_list.append(message.author.id)
            if message.author.id in main_dict[message.guild.id].skip_vote:
                main_dict[message.guild.id].skip_vote.remove(message.author.id)
            await main_dict[message.guild.id].update_log('ignore_on', message.author.name)
        else:
            main_dict[message.guild.id].ignore_list.remove(message.author.id)
            await main_dict[message.guild.id].update_log('ignore_off', message.author.name)
    except:
        pass


async def dm_info(message):
    quiz = main_dict[message.guild.id]
    if not quiz:
        return
    if not quiz.song:
        await message.author.send("There are no songs right now so we cannot get info")
        return
    if quiz.display_eng == "?" and message.author.id not in quiz.correct_list:
        await message.author.send(
            "We can only send you the information if the answer is shown or you answered correctly")
        return

    info_message = f'''**{quiz.song.song_name}**'s info
Server: {quiz.song.servers}

'''

    for key, value in quiz.song.lyrics_dict.items():
        info_message += f'-----\n{key}:\n'
        info_message += value
        info_message += '\n'

    string = info_message
    length = 1999
    for part in [string[i:length + i] for i in range(0, len(string), length)]:
        await message.author.send(part)


command_dict = {
    "music": musicgui,
    "ignore": toggle_ignore,
    "info": dm_info
}


async def initiate_message():
    await asyncio.sleep(3)
    for guild in bot.guilds:
        for text_channel in guild.text_channels:
            if text_channel.name == 'bangdream':
                try:
                    message = await text_channel.send('Starting bot...')
                    await musicgui(message)
                except discord.errors.Forbidden:
                    pass
                except:
                    logger.exception(f'failed to initiate message')


def setup(bot):
    bot.add_cog(QuizGUI(bot))
