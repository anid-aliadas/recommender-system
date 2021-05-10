from .dependencies import config
from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient

#Mongo instantiation

client = AsyncIOMotorClient(config('MONGO_ENDPOINT'))
engine = AIOEngine(motor_client=client, database=config('MONGO_DATABASE'))