from fastapi import APIRouter, WebSocket, Request
from containers.container_manager import ContainerManager
from containers.docker_container_manager import DockerContainerManager
from containers.container_manager_spaw import ContainerManagerSpaw
from containers.command_manager import CommandManager
from core.logger import logger
from .models.models import CommandRequest, ContainerUp, CommandResponse
from api.websocket_manager import ws_manager
from core.config import settings
import json

container_router = APIRouter()
manager = ContainerManager()
manager_docker = CommandManager()#ContainerManagerSpaw()# DockerContainerManager()

@container_router.post("/", response_model=CommandResponse)
async def lauch_acl2_container(request: Request):
    raw_body = await request.body()  # Obtiene el cuerpo crudo de la petición
    decoded_body = raw_body.decode("utf-8", errors="replace")  # Decodifica el cuerpo como UTF-8
    logger.info(f"Raw input: {repr(decoded_body)}")  # Muestra caracteres ocultos
    """ Endpoint to launch an ACL2 instance"""
    json_data = json.loads(decoded_body) 
    id = json_data.get("user_id", "")
    status = True
    if settings == "podman":
        status =await manager.start_acl2_container(id)
    else:
        status = await manager_docker.start_acl2_container(id)
    return status

@container_router.post("/execute/", response_model=CommandResponse)
async def execute_acl2(request: Request):
    """ Endpoint to execute an ACL2 command and get the response """
    
    raw_body = await request.body()  # Obtiene el cuerpo crudo de la petición
    decoded_body = raw_body.decode("utf-8", errors="replace")  # Decodifica el cuerpo como UTF-8
    logger.info(f"Raw input: {repr(decoded_body)}")  # Muestra caracteres ocultos
    """ Endpoint to launch an ACL2 instance"""
    json_data = json.loads(decoded_body) 
    id = json_data.get("user_id", "")
    cmd = json_data.get("command", "")
    if settings == "podman":
        output = await manager.send_command(cmd, id)
    else:
        output = await manager_docker.send_command(cmd, id)
    return output

@container_router.get("/formulas/{user_id}", response_model=CommandResponse)
async def get_current_formulas(user_id):
    """ Endpoint to get current ACL2 formulas"""
    logger.info(f"Getting the current formulas for user: {user_id}")
    id = user_id
    if settings == "podman":
        output = await manager.send_command(":pbt 0", id)
    else:
        output = await manager.send_command(":pbt 0", id)
    return output