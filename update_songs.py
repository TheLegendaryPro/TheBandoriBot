import json
import logging
# create logger with 'spam_application'
from pathlib import Path
import shutil

logger = logging.getLogger('update_songs')
logger.setLevel(logging.INFO)
# create file handler which logs even debug messages
fh = logging.FileHandler('update_songs.log')
fh.setLevel(logging.INFO)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


def load_data():
    with open('bot_data/song_id_data.json', 'r') as f:
        data = json.load(f)
    return data


def find_game_version(path):
    # Check if only have one file, if so, use it
    file_count = 0
    for file_path in path.iterdir():
        game_version_path = file_path
        file_count += 1
    if file_count == 1:
        return game_version_path

    # Check if only one game version, if so, use it
    have_game = []
    for file_path in path.iterdir():
        if 'game ver' in str(file_path.name).lower() or 'game size' in str(file_path.name).lower():
            have_game.append(file_path)
            game_version_path = file_path
    if len(have_game) == 1:
        return game_version_path
    if len(have_game) > 1:
        # Have two or more game version, return the one with shorter name
        for file_path in have_game:
            if len(file_path.name) < len(game_version_path.name):
                game_version_path = file_path
        logger.warning(f"Found two or more game version for {path.name}, using {game_version_path}")
        return game_version_path

    # Have to guess based on the shortest name
    for file_path in path.iterdir():
        if len(file_path.name) < len(game_version_path.name):
            game_version_path = file_path
    logger.warning(f"Have no clue what to use for {path.name}, using {game_version_path}")
    return game_version_path


def copy_file(game_version_path, data):
    for item in data:
        if item['id'] == game_version_path.parent.name:
            try:
                shutil.copy(game_version_path, 'song_id_files/' + item['id'] + '.ogg')
            except:
                logger.warning(f"Failed to copy {game_version_path.name}")


def copy_all_songs(data, path):
    p = Path(path)
    subdir_list = [x for x in p.iterdir() if x.is_dir()]

    for path in subdir_list:
        game_version_path = find_game_version(path)
        copy_file(game_version_path, data)




def main():
    path = r'D:\OneDrive - HKUST Connect\Python\scrape_bandori_fandom\song_files'
    logger.info('started update_songs')
    data = load_data()
    copy_all_songs(data, path)
    #loop through files from id
    #find the one with game version, or the shortist


if __name__ == '__main__':
    main()