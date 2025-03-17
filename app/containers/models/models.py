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

    def update(self, container_id: str = None, status: bool = None, user_id: str = None):
        updates = {
            "container_id": container_id.lstrip().strip() if container_id is not None else self.container_id,
            "status": status if status is not None else self.status,
            "user_id": user_id.lstrip().strip() if user_id is not None else self.user_id,
            "update_at": datetime.now().timestamp()
        }
        return self.model_copy(update=updates)
    
class CommandRequest(BaseModel):
    container_id: Optional[str] = ""
    command: str
    user_id: Optional[str] = None

class ContainerUp(BaseModel):
    user_id: str

class CommandResponse(BaseModel):
    container_id: Optional[str] = None
    command: str
    output: str
    user_id: Optional[str] = None
    ok: bool = True
    ws_url: Optional[str] = None