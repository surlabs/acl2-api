from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId
from core.database import containers_collection
from core.logger import logger
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator


PyObjectId = Annotated[str, BeforeValidator(str)]
    
class ContainerInfo(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    container_id: str | None = None
    status: bool = False
    user_id: str | None = None

    async def find_myself(self):
        updated_document = await containers_collection.find_one({"_id": ObjectId(self.id)})
        if res:
            updated_document["id"] = str(updated_document.pop("_id"))
            res = ContainerInfo(**res)

    def update(self, container_id: str = None, status: bool = None, user_id: str = None):
        updates = {
            "container_id": container_id.lstrip() if container_id is not None else self.container_id,
            "status": status if status is not None else self.status,
            "user_id": user_id.lstrip() if user_id is not None else self.user_id
        }
        return self.model_copy(update=updates)
    
    async def save(self):
        res = None
        if self.id is None:
            result = await containers_collection.insert_one(self.model_dump(exclude=["id"]))
            self.id = str(result.inserted_id)  # Guardar el ID generado
        else:
            await containers_collection.update_one(
                {"_id": ObjectId(self.id)},
                {"$set": self.model_dump(exclude=["id"])}
            )
        updated_document = await containers_collection.find_one({"_id": ObjectId(self.id)})
        if updated_document:
            res = ContainerInfo(**updated_document)

        return res