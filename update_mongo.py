import asyncio

import motor.motor_asyncio
import json
from utils.mongo import Document

with open('bot_config/secrets.json', 'r') as f:
    data = json.load(f)
    connection_url = data['mongo']

mongo = motor.motor_asyncio.AsyncIOMotorClient(str(connection_url))
db = mongo["TheBandoriBot"]
config = Document(db, "user_db")

with open('bot_data/user_db.json') as f:
    user_db = json.load(f)


async def main():
    for value in user_db["_default"].items():
        data = value[1]
        data['_id'] = data.pop('user_id')
        print(data)
        await config.upsert(data)


newfeature = asyncio.get_event_loop().run_until_complete(main())