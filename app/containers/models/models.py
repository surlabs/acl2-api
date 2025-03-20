from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]
    
class CommandInfo(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    status: bool = False
    user_id: str | None = None
    insert_at: float = Field(default_factory=datetime.now().timestamp) 
    update_at: float = Field(default_factory=datetime.now().timestamp)

    def update(self, status: bool = None, user_id: str = None):
        updates = {
            "status": status if status is not None else self.status,
            "user_id": user_id.lstrip().strip() if user_id is not None else self.user_id,
            "update_at": datetime.now().timestamp()
        }
        return self.model_copy(update=updates)
    
class CommandRequest(BaseModel):
    container_id: Optional[str] = ""
    command: str
    user_id: Optional[str] = None

class ProcessUp(BaseModel):
    user_id: str

class CommandResponse(BaseModel):
    container_id: Optional[str] = None
    command: str
    output: str
    user_id: Optional[str] = None
    ok: bool = True
    ws_url: Optional[str] = None

class Acl2CheckerResponse(BaseModel):
    container_id: Optional[str] = None
    command: str
    output: str
    user_id: Optional[str] = None
    ok: bool = True
    correct: bool = False
