import asyncio

import motor.motor_asyncio
import json
from utils.mongo import Document

with open('bot_config/secrets.json', 'r') as f:
    data = json.load(f)
    connection_url = data['mongo']

mongo = motor.motor_asyncio.AsyncIOMotorClient(str(connection_url))
db = mongo["TheBandoriBot"]
config = Document(db, "server_config")

with open('bot_config/prefixes.json') as f:
    prefix_data = json.load(f)


async def main():
    for key, value in prefix_data.items():
        await config.upsert({"_id": int(key), "prefix": value})


newfeature = asyncio.get_event_loop().run_until_complete(main())