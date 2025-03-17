from fastapi import APIRouter, WebSocket
from containers.container_manager import ContainerManager
from containers.docker_container_manager import DockerContainerManager
from core.logger import logger
from .models.models import CommandRequest, ContainerUp
from api.websocket_manager import ws_manager
from core.config import settings

container_router = APIRouter()
manager = ContainerManager()
manager_docker = DockerContainerManager()

@container_router.post("/")
async def lauch_acl2_container(container_up: ContainerUp):
    """ Endpoint to launch an ACL2 instance"""
    id = container_up.user_id
    status = True
    if settings == "podman":
        status =await manager.start_acl2_container(id)
    else:
        status = await manager_docker.start_acl2_container(id)
    return status

@container_router.post("/execute/")
async def execute_acl2(command_request: CommandRequest):
    """ Endpoint to execute an ACL2 command and get the response """
    cmd = command_request.command
    id = command_request.user_id
    if settings == "podman":
        output = await manager.send_command(cmd, id)
    else:
        output = await manager_docker.send_command(cmd, id)
    return output

@container_router.get("/formulas/{user_id}")
async def get_current_formulas(user_id):
    """ Endpoint to get current ACL2 formulas"""
    logger.info(f"Getting the current formulas for user: {user_id}")
    id = user_id
    if settings == "podman":
        output = await manager.send_command(":pbt 0", id)
    else:
        output = await manager.send_command(":pbt 0", id)
    return output