from fastapi import APIRouter, WebSocket
from containers.container_manager import ContainerManager
from core.logger import logger
from .models.models import CommandRequest, ContainerUp
from api.websocket_manager import ws_manager

container_router = APIRouter()
manager = ContainerManager()

@container_router.post("/")
async def lauch_acl2_container(container_up: ContainerUp):
    """ Endpoint to launch an ACL2 instance"""
    id = container_up.user_id
    status = True
    #await manager.start_acl2_container_docker(id)
    #status = await manager.start_acl2_container(id)
    await manager.start_docker()
    return status

@container_router.post("/execute/")
async def execute_acl2(command_request: CommandRequest):
    """ Endpoint to execute an ACL2 command and get the response """
    cmd = command_request.command
    id = command_request.user_id
    output = await manager.send_command(cmd, id)
    #output = await manager.send_command_docker(cmd, id)
    return output

@container_router.get("/formulas/{user_id}")
async def get_current_formulas(user_id):
    """ Endpoint to get current ACL2 formulas"""
    logger.info(f"Getting the current formulas for user: {user_id}")
    id = user_id
    output = await manager.send_command(":pbt 0", id)
    return output