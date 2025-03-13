from fastapi import APIRouter
from containers.container_manager import ContainerManager
from core.logger import logger
from .models.models import CommandRequest, ContainerUp

container_router = APIRouter()
manager = ContainerManager()

@container_router.post("/")
async def lauch_acl2_container(container_up: ContainerUp):
    """ Endpoint to launch an ACL2 instance"""
    id = container_up.user_id
    status = await manager.start_acl2_container(id)
    return status

@container_router.post("/execute/")
async def execute_acl2(command_request: CommandRequest):
    """ Endpoint to execute an ACL2 command and get the response """
    logger.info(f"Running the command: {command_request.command} in container: {command_request.container_id}")
    cmd = command_request.command
    id = command_request.user_id
    output = manager.send_command(cmd, id)
    return output

@container_router.get("/formulas/{user_id}")
async def get_current_formulas(command_request: CommandRequest):
    """ Endpoint to get current ACL2 formulas"""
    logger.info(f"Running the command: {command_request.command} in container: {command_request.container_id}")
    id = command_request.user_id
    output = manager.send_command(":pbt 0", id)
    return output