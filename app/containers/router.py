from fastapi import APIRouter
from containers.container_manager import ContainerManager
import json

container_router = APIRouter()

@container_router.post("/")
async def lauch_acl2_container():
    manager = ContainerManager()
    status = await manager.start_acl2_container()
    return status