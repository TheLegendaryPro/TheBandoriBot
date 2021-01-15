# TheBandoriBot

A Discord quiz bot about BanG Dream Songs

## Commands.py
stats: to check stats
logout: for owner to logout
prefix: for admin to change prefix
show_help: to show help
testadd: for owner to test if the db is working
setchannel: for mods to set what channel the bot connects to

## Shop.py
3 helper function:
get_db: get the data from the db, if not, tell the user
set_db: upsert a property to the db
add_db: increase a property to the db

shop: show what the user can buy
buy: decrease the currency and give user the item
equip: change user's active item
printdb: for owner to check a player's data
leaderboard: show the leaderboard of stars
addstars: for owner to add stars to users
cleandatabase: for owner to remove faulty data in db
gacha: wip command to randomly draw items

## Quizgui.py
1 helper function:
is_similar: to check if the input from user is similar to the song name (answer)

Musicgui
get_embed: create the embed object and return it
create_message: send the message
play_song: check channel, then client, then play song, and set up timers
give_hint: Generate a hint and send it
show answer: shows the answer
next_song: the callback for next timer
skip_song: check for votes, then skip the song
toggle_autoplay: toggle and announce autoplay
cancel_all_timers: cancle all timers on a guild
check_star: tell the user how much star he have
leave_channel: leaves the voice channel
update_log: function for processing the log
update_message: simple function to reload the message
correct_song: called when the answer is correct, add the stars
correct_band: called when the user got the band correct
add_points: to add points to a user

Song
init: generate a random song and set its detials

timer
init: set the time and task
job: do the task
cancel: not do it

other helper functions:
call_gui: when have to initaite the game
process_message: process the message that was sent in bangdream channel
start_cooldown: ???
process_reaction: react to reactions

Quizgui
on_reaction_add: check if have to react, then call process_reaction
on_resume: apparently things break when discord resumes, so we restart when it resumes
on_voice_state_update: check if need to leave whenever someone leave or join
on_message: check if we have to process the message, then process it

other helper functions
musicgui: to call the musicgui
resend_message: supposed to solve the problem on_resume solved
toggle_ignore: to toggle whether skip vote is ignored for a player
dm_info: to send the current song's info
initiate_message: to send the first message