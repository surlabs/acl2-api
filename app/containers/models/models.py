from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId
from core.database import containers_collection
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator
from datetime import datetime


PyObjectId = Annotated[str, BeforeValidator(str)]
    
class ContainerInfo(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    container_id: str | None = None
    status: bool = False
    user_id: str | None = None
    insert_at: float = Field(default_factory=datetime.now().timestamp) 
    update_at: float = Field(default_factory=datetime.now().timestamp)

    async def find_myself(self):
        updated_document = await containers_collection.find_one({"_id": ObjectId(self.id)})
        if updated_document:
            updated_document["id"] = str(updated_document.pop("_id"))
            res = ContainerInfo(**updated_document)
            return res

    def update(self, container_id: str = None, status: bool = None, user_id: str = None):
        updates = {
            "container_id": container_id.lstrip().strip() if container_id is not None else self.container_id,
            "status": status if status is not None else self.status,
            "user_id": user_id.lstrip().strip() if user_id is not None else self.user_id,
            "update_at": datetime.now().timestamp()
        }
        return self.model_copy(update=updates)
    
    async def save(self):
        res = None
        if self.id is None:
            result = await containers_collection.insert_one(self.model_dump(exclude=["id"]))
            self.id = str(result.inserted_id)
        else:
            await containers_collection.update_one(
                {"_id": ObjectId(self.id)},
                {"$set": self.model_dump(exclude=["id"])}
            )
        updated_document = await containers_collection.find_one({"_id": ObjectId(self.id)})
        if updated_document:
            res = ContainerInfo(**updated_document)

        return res
    
class CommandRequest(BaseModel):
    container_id: str
    command: str

class ContainerUp(BaseModel):
    container_id: str

class CommandResponse(BaseModel):
    container_id: Optional[str] = None
    command: str
    output: str
    user_id: str
    ok: bool = True