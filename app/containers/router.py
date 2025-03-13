from fastapi import APIRouter
from containers.container_manager import ContainerManager
from core.logger import logger
from .models.models import CommandRequest, ContainerUp

container_router = APIRouter()
manager = ContainerManager()

@container_router.post("/")
async def lauch_acl2_container(containerUp: ContainerUp):
    """ Endpoint to launch an ACL2 instance"""
    id = containerUp.container_id
    status = await manager.start_acl2_container(id)
    return status

@container_router.post("/execute/")
async def execute_acl2(commandRequest: CommandRequest):
    """ Endpoint to execute an ACL2 command and get the response """
    logger.info(f"Running the command: {commandRequest.command} in container: {commandRequest.container_id}")
    cmd = commandRequest.command
    id = commandRequest.container_id
    #output = manager.send_acl2_command(id, cmd)
    output = manager.send_command(cmd, id)
    return output