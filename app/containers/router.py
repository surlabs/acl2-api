from fastapi import APIRouter
from containers.command_manager import CommandManager
from core.logger import logger
from .models.models import CommandRequest, ProcessUp, CommandResponse, Acl2CheckerResponse

container_router = APIRouter()
manager = CommandManager()

@container_router.post("/", response_model=CommandResponse)
async def lauch_acl2_container(process_up: ProcessUp):
    """Endpoint to launch an ACL2 instance"""
    
    status = await manager.start_acl2_process(process_up)
    
    return status

@container_router.post("/execute/", response_model=CommandResponse)
async def execute_acl2(command_request: CommandRequest):
    """ Endpoint to execute an ACL2 command and get the response """
    
    cmd = command_request.command
    id = command_request.user_id
    output = await manager.send_command(cmd, id)
    
    return output

@container_router.get("/formulas/{user_id}", response_model=CommandResponse)
async def get_current_formulas(user_id):
    """ Endpoint to get current ACL2 formulas"""
    
    logger.info(f"Getting the current formulas for user: {user_id}")
    id = user_id
    output = await manager.send_command(":pbt 0", id)
    return output

@container_router.post("/check/", response_model=Acl2CheckerResponse)
async def check_answer(command_request: CommandRequest):
    """ Endpoint to check the ACL2 answer """
    
    cmd = command_request.command
    id = command_request.user_id
    output = await manager.check_solution(cmd, id)
    
    return output