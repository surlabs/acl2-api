from bson import ObjectId
from core.database import commands_collection
from containers.models.models import CommandInfo
from datetime import timedelta, datetime
from core.logger import logger
from core.config import settings

class CommandRepo:

    async def find_one(self, id: str) -> None|CommandInfo:
        res = None
        updated_document = await commands_collection.find_one({"_id": ObjectId(id)})
        if updated_document:
            res = CommandInfo(**updated_document)
        return res
        
    async def find_one_by_user_id(self, id: str, status: bool) -> None|CommandInfo:
        res = None
        updated_document = await commands_collection.find_one({"user_id": id, "status": status})
        if updated_document:
            res = CommandInfo(**updated_document)
        return res

    async def save(self, container_info: CommandInfo) -> CommandInfo | None:
        res = None
        if container_info.id is None:
            result = await commands_collection.insert_one(container_info.model_dump(exclude=["id"]))
            container_info.id = str(result.inserted_id)
        else:
            await commands_collection.update_one(
                {"_id": ObjectId(container_info.id)},
                {"$set": container_info.model_dump(exclude=["id"])}
            )
        res = await self.find_one(container_info.id)

        return res
    
    async def get_commands_with_no_interactions(self) -> list[CommandInfo]:
        res = None
        now_timestamp = datetime.now().timestamp()
        time_ago = now_timestamp - settings.PROCESS_VALID_PERIOD_IN_SECONDS

        query = {
            "update_at": {"$lte": time_ago},
            "status": True
        }

        res = await commands_collection.find(query).to_list()

        return res
    
    async def delete_one(self, container_info: CommandInfo):
        await commands_collection.delete_one({"_id": ObjectId(container_info.id)})

    
command_repo = CommandRepo()