from bson import ObjectId
from core.database import containers_collection
from containers.models.models import ContainerInfo
from datetime import timedelta, datetime
from core.logger import logger
from core.config import settings

class ContainerRepo:

    async def find_one(self, id: str) -> None|ContainerInfo:
        res = None
        updated_document = await containers_collection.find_one({"_id": ObjectId(id)})
        if updated_document:
            res = ContainerInfo(**updated_document)
        return res
        
    async def find_one_by_user_id(self, id: str, status: bool) -> None|ContainerInfo:
        res = None
        updated_document = await containers_collection.find_one({"user_id": id, "status": status})
        if updated_document:
            res = ContainerInfo(**updated_document)
        return res

    async def save(self, container_info: ContainerInfo):
        res = None
        if container_info.id is None:
            result = await containers_collection.insert_one(container_info.model_dump(exclude=["id"]))
            container_info.id = str(result.inserted_id)
        else:
            await containers_collection.update_one(
                {"_id": ObjectId(container_info.id)},
                {"$set": container_info.model_dump(exclude=["id"])}
            )
        res = await self.find_one(container_info.id)

        return res
    
    async def get_containers_with_no_interactions(self):
        res = None
        now_timestamp = datetime.now().timestamp()
        time_ago = now_timestamp - settings.CONTAINER_VALID_PERIOD_IN_SECONDS

        query = {
            "update_at": {"$lte": time_ago},
            "status": True
        }

        res = await containers_collection.find(query).to_list()

        return res
    
    def delete_one(self, container_info: ContainerInfo):
        containers_collection.delete_one({"_id": ObjectId(container_info.id)})

    
container_repo = ContainerRepo()