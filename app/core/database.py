from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

# Conectar a la base de datos
client = AsyncIOMotorClient(settings.DATABASE_URL)
database = client[settings.DATABASE_NAME]
containers_collection = database.get_collection("containers")
commands_collection = database.get_collection("commands")
