from pathlib import Path
from tinydb import TinyDB, Query
from tinydb.operations import add
import json


cwd = Path(__file__).parents[1]
cwd = str(cwd)
db = TinyDB(cwd + '/bot_data/user_db.json', indent=4)

# db.truncate()
#
# with open(cwd + '/bot_data/' + 'user_data'+ '.json', 'r') as file:
#     data = json.load(file)
#
# for key, item in data.items():
#     one_dict = {'user_id': int(key)}
#     if 'points' in item:
#         one_dict['stars'] = item['points']
#     if 'name' in item:
#         one_dict['username'] = item['name']
#     if 'discriminator' in item:
#         one_dict['discriminator'] = item['discriminator']
#     db.insert(one_dict)

result = db.search(Query().user_id == 1234)
value1 = db.update(add("stars", 0), Query().user_id == 1234)
print(value1)
print(result)
