from fastapi import APIRouter
from containers.container_manager import ContainerManager
from core.logger import logger
from .models.models import CommandRequest, ContainerUp

container_router = APIRouter()
manager = ContainerManager()

@container_router.post("/")
async def lauch_acl2_container(containerUp: ContainerUp):
    id = containerUp.container_id
    status = await manager.start_acl2_container(id)
    return status

@container_router.post("/execute/")
async def execute_acl2(commandRequest: CommandRequest):
    """ Endpoint para ejecutar un comando en ACL2 dentro del contenedor y devolver la salida """
    logger.info(f"Ejecutando el comando: {commandRequest.command} en el contenedor: {commandRequest.container_id}")
    cmd = commandRequest.command
    id = commandRequest.container_id
    #output = manager.send_acl2_command(id, cmd)
    output = manager.send_command(cmd, id)
    return output