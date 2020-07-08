import discord
from discord.ext import commands
import asyncio
import cogs._json
import random
# For check simular
import jellyfish
# For audio length
import audioread
import datetime



main_dict = {
"guild_id": "MusicQuiz object"
}


def is_similar(input, answer):
    if jellyfish.jaro_winkler_similarity(input, answer) > 0.8:
        if (abs(len(input)-len(answer)) / max(len(input), len(answer))) < 0.2:
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
        self.log = ["React <:KokoroYay:727683024526770222> to start! Type the answer in chat below <:SayoYay:714494329779126392>"]
        self.hint_timer = "timer object"
        self.answer_timer = "timer object"
        self.auto_play = False
        self.next_timer = "timer object"
        self.servers = "all"
        self.skip_vote = []
        self.correct_list = []


    def get_embed(self):
        '''create the embed object and return it'''
        embed = discord.Embed(title='Press <:KokoroYay:727683024526770222> to start!', description='\uFEFF')
        embed.add_field(inline=False, name = "Instructions",value='''
        Guess the song/band of the playing song and earn <:StarGem:727683091337838633>s!
        Press <:AyaPointUp:727496890693976066>: vote skip, <:StarGem:727683091337838633>: check star''')
        embed.add_field(name="Song Name: ", value=f'''{self.display_eng}
        {self.display_jp}''')
#        embed.add_field(name="English Name: ", value=self.display_eng)
#        embed.add_field(name='Japanese Name:', value=self.display_jp)
        embed.add_field(name='Band: ', value=self.display_band)
        embed.add_field(name="Difficulty", value=f"Expert: {self.display_expert} - Special: {self.display_special}")
        # embed.add_field(name='Special difficulty: ', value=self.display_special)
        #embed.add_field(name='Type', value=self.display_type)

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
        embed.set_author(name="Made by TheLegendaryPro#6810", icon_url="https://cdn.discordapp.com/avatars/298986102495248386/c36840dfbed5e0e27253ada30eb1dedf.webp?size=128")

        return embed


    async def create_message(self):
        msg_cont = "Welcome to BanG Dream Music Quiz"
        embed = self.get_embed()
        self.message = await self.t_channel.send(content=msg_cont, embed=embed)
        for item in react_dict.keys():
            await self.message.add_reaction(item)


    async def play_song(self, user):
        # Try to save data
        await self.save_data()

        try:
            voice_channel = user.voice.channel
        except:
            # except user is not in a voice channel
            await self.update_log(f"Hey {user.name}, get into voice channel first then click <:KokoroYay:727683024526770222> again")
            return
        if self.v_channel == "voice channel":
            # Not connect yet
            self.v_client = await voice_channel.connect()
            self.v_channel = voice_channel
        elif self.v_channel != voice_channel:
            # Connected to wrong one
            await self.v_client.move_to(voice_channel)
            self.v_channel = voice_channel

        # toggle auto play if a song is already playing
        if self.v_client.is_playing():
            await self.toggle_autoplay(user)
            return
        # elif self.v_client.is_paused():
        #     await self.update_log("I'm paused, press ⏸️ to continue paying")
        #     return
        else:
            self.song = Song(self)


        # Start the player to play a song
        def load_success():
            print(f"loaded {ascii(self.song.song_name)}")
            # I wanted to make it stopped when the audio stopeed, failed
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

        self.display_eng = self.song.song_name
        self.display_jp = self.song.name_jp
        self.display_band = self.song.band_name
        self.display_expert = self.song.expert
        self.display_special = self.song.special
        self.display_type = self.song.type
        await self.update_log(f"Time's up, the song was {self.song.song_name}")
        del self.answer_timer


    async def next_song(parameters):
        self, user = parameters
        await self.play_song(user)


    # async def pause(self, user):
    #     # cancel the next timer
    #     try:
    #         self.next_timer.cancel()
    #     except:
    #         pass
    #     try:
    #         if self.v_client.is_paused():
    #             self.v_client.resume()
    #             await self.update_log(f"{user.name} resumed the player")
    #         else:
    #             self.v_client.pause()
    #             await self.update_log(f"{user.name} paused the player")
    #             await self.update_log(f"auto play stopped because you paused")
    #     except:
    #         await self.update_log("Cannot pause becasue no song is playing")


    async def skip_song(self, user):
        # See if the voice client is playing anythong
        try:
            self.v_client.is_playing()
        except:
            await self.update_log("Cannot skip becasue no song is playing")
            return
        # See if everyone agreed
        if user.id not in self.skip_vote:
            self.skip_vote.append(user.id)
        for user_id in [user.id for user in self.v_channel.members if user.id != 650352975839100947]:
            if user_id in self.skip_vote:
                pass
            else:
                await self.update_log(f"{user.name} voted to skip, but not everyone agreed ({len(self.skip_vote)}/{len([user.id for user in self.v_channel.members if user.id != 650352975839100947])})")
                return
        # Actually skip the song
        print([user.id for user in self.v_channel.members if user.id != 650352975839100947], self.skip_vote, "skipping a song")
        await self.update_log(f"song skipped by {user.name}, Will play another song soon")
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
        self.auto_play = not self.auto_play
        await self.update_log(f"auto play is set to {self.auto_play} by {user.name}")

    async def check_star(self, user):
        if user.id not in song_points:
            await self.update_log(f"Hey {user.name}, you don't have any <:StarGem:727683091337838633> yet, try answer songs correctly")
        else:
            star = song_points[user.id]
            await self.update_log(f"Hi {user.name}, you have {star} <:StarGem:727683091337838633>, congratulation!")


    async def leave_channel(self, user):
        key = str(self.t_channel.id) + "leave"
        if key in cooldown_dict:
            await self.update_log(f"Hey {user.name}, the shutdown function is still on cooldown, if the bot is not working feel free to ping the creator")
            return
        else:
            x = Timer(150, start_cooldown, key)
            cooldown_dict[key] = "2"
        # Leave the channel and delete all timers
        if not isinstance(self.v_client, str):
            # Reset some variables
            await self.v_client.disconnect()
            self.v_client = "voice client object"
            self.v_channel = "voice channel"
        else:
            await self.update_log(f"{user.name} asked me to leave, but I'm not in a voice channel")
            return
        # Try to cancel timers
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
            cogs._json.write_json(song_usage_data, "song_usage_data")
            cogs._json.write_json(song_points, "song_points")
            return
        key = str(self.t_channel.id) + "save"
        if key in cooldown_dict:
            await self.update_log(f"Hey {user.name}, the save data function is still on cooldown")
            return
        else:
            x = Timer(30, start_cooldown, key)
            cooldown_dict[key] = "3"
        cogs._json.write_json(song_usage_data, "song_usage_data")
        cogs._json.write_json(song_points, "song_points")
        if user.id == 298986102495248386:
            await self.update_log("<:AyaWow:728185928199307317> Se-senpai, da-data is s-saved")
        else:
            await self.update_log(f"You-you're not my senpai, {user.name}, but the data is still saved")


    async def update_log(self, event):
        if len(self.log) >= 7:
            del self.log[0]
        self.log.append(event)
        await self.update_message()


    async def update_message(self):
        embed = self.get_embed()
        await self.message.edit(embed = embed)


    async def correct_song(self, user):
        if len(self.correct_list) == 0:
            if user.id in song_points:
                song_points[user.id] += 2
            else:
                song_points[user.id] = 2
            await self.update_log(f"{user.name} was first to guess the song name, earning <:StarGem:727683091337838633><:StarGem:727683091337838633>")
            self.correct_list = [user.id]
        else:
            if user.id not in self.correct_list:
                if user.id in song_points:
                    song_points[user.id] += 1
                else:
                    song_points[user.id] = 1
                await self.update_log(f"{user.name} got it correct too, earning <:StarGem:727683091337838633>")
                self.correct_list.append(user.id)
            else:
                await self.update_log(f"{user.name}, you already answered, why would you answer again?")


    async def correct_band(self, user):
        if user.id in song_points:
            song_points[user.id] += 1
        else:
            song_points[user.id] = 1
        self.display_band = self.song.band_name
        await self.update_log(f"{user.name} got the band right and earned 1 <:StarGem:727683091337838633>")


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

        #song_usage_data["played"][choose]["attempt"] = int(song_usage_data["played"][choose]["attempt"]) + 1
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
song_usage_data = cogs._json.read_json("song_usage_data")

# Get and fix user data
song_points_raw = cogs._json.read_json("song_points")
song_points = {}
for i in song_points_raw.keys():
    try:
        song_points[int(i)] = song_points_raw[i]
    except:
        print("failed decode song point raw")
        pass

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
        # Delete up to 10 message to clear up bangdream text channel
        if message.channel.name == "bangdream":
            await message.channel.purge(limit=10)
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
        if not (quiz.v_client.is_playing() or quiz.v_client.is_paused()):
            need_check_ans = False

    # see if the answer was answered, if no, check
    if need_check_ans:
        if quiz.display_eng == "?":
            if is_similar(message.content,quiz.song.song_name):
                await quiz.correct_song(message.author)
                return
            if is_similar(message.content,quiz.song.name_jp) and quiz.song.name_jp != "same as english name":
                await quiz.correct_song(message.author)
                return
            if is_similar(message.content,quiz.song.translation) and quiz.song.translation != "no translation":
                await quiz.correct_song(message.author)
                return
            if is_similar(message.content.lower(),quiz.song.song_name.lower()):
                await quiz.update_log(f"{message.author.name} were close, try again by adding / remove CAPITAL LETTERS")
                return

        # see if the band name was answered, if no, check
        if quiz.display_band == "?":
            if is_similar(message.content,quiz.song.band_name):
                await quiz.correct_band(message.author)
                return
    # Get rid of new line
    no_new_line = message.content.replace('\n', '')
    with open("bot_config/chatlog.txt", "a", encoding="UTF-8") as f:
        f.write(f"\n{datetime.datetime.now()} {str(message.author)}: {no_new_line}")
    await quiz.update_log(f"{str(message.author)[:-5]}: {no_new_line[:150]}")


# The function to deal with reactions and know what to do
react_dict={
"<:KokoroYay:727683024526770222>": MusicQuiz.play_song,
"<:AyaPointUp:727496890693976066>": MusicQuiz.skip_song,
#"<:RinkoHide:727683091182649457>": MusicQuiz.toggle_autoplay,
"<:StarGem:727683091337838633>": MusicQuiz.check_star,
#"<:MocaStarNom:727683091409404005>": MusicQuiz.save_data,
#"<:YukinaDab:727683091350421605>": MusicQuiz.leave_channel
}

# A dict for reaction cooldown
cooldown_dict = {
"key": "random int"
}


async def start_cooldown(key):
    del cooldown_dict[key]


async def process_reaction(reaction, user):
    if user.id in cooldown_dict:
        await reaction.remove(user)
        return
    else:
        x = Timer(5, start_cooldown, user.id)
        cooldown_dict[user.id] = "1"

    if reaction.message.id == main_dict[reaction.message.guild.id].message.id:
        if reaction.count > 2:
            await reaction.remove(user)
            return
        await react_dict[str(reaction.emoji)](main_dict[reaction.message.guild.id], user)
        await reaction.remove(user)






class QuizGUI(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} Cog has been loaded\n-----")


    # @commands.command(aliases = ["mg"])
    # async def musicgui(self, message):
    #     if message.channel.name == "bangdream":
    #         await call_gui(ctx)

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
        if reaction.message.channel.name == "bangdream":
            if user.id != 650352975839100947:
                if user.id in self.bot.blacklisted_users:
                    await reaction.remove(user)
                    return
                await process_reaction(reaction, user)


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



    # @commands.command()
    # @commands.is_owner()
    # async def purgebangdream(self, ctx):
    #     msg = f"{ctx.channel.name}"
    #     await ctx.send(msg)
    #     if ctx.channel.name == "bangdream":
    #         await ctx.channel.purge(limit=10)



    @commands.Cog.listener()
    async def on_message(self, message):
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


command_dict = {
"start": musicgui,
"mg": musicgui
}



def setup(bot):
    bot.add_cog(QuizGUI(bot))
