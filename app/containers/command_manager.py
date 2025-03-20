import subprocess
import asyncio
from datetime import datetime, timedelta
from core.config import settings
from core.logger import logger
from .models.models import CommandInfo, CommandResponse, Acl2CheckerResponse
from .models.structures import ContainerInstance, CommandInstance
from api.websocket_manager import ws_manager
from .repository.command_repo import command_repo
from .acl2_manager import Acl2Manager

acl2_manager = Acl2Manager()

class CommandManager:

    def __init__(self):
        self.acl2_image = settings.ACL2_CONTAINER_NAME
        self.containers: dict[str, CommandInstance] = {}

    async def update_command_info_last_interaction(self, object_id: str) -> CommandInfo | None:
        container_info = await command_repo.find_one(object_id)
        if container_info is not None:
            container_info = container_info.update()
            return await command_repo.save(container_info)
        else:
            logger.error(f"Container not found: {object_id}")
            return None
    
    async def read_lines_acl2(self, user_id: str):
        output = []
        proc = self.containers[user_id].process

        timeout = 1.0
        buffer = ""

        try:
            while True:
                char = await asyncio.wait_for(asyncio.to_thread(proc.stdout.read, 1), timeout=timeout)
                if not char:
                    break
                
                buffer += char 
                
                if char == "\n" or "ACL2 !>" in buffer:
                    clean_line = buffer.strip()
                    logger.info(f"*{clean_line}*")
                    output.append(clean_line)
                    await ws_manager.send_message(user_id=user_id, message=clean_line)
                    
                    if "ACL2 !>" in clean_line:
                        break

                    buffer = ""  

        except asyncio.TimeoutError:
            logger.debug(f"Line readen for user {user_id}")

        return "\n".join(output)
        
    async def stop_container(self, object_id: str):
        container_info = await command_repo.find_one(object_id)
        if container_info is None:
            logger.error(f"Container not found: {object_id}")
            return
        self.containers[container_info.user_id].process.terminate()
        try:
            await asyncio.to_thread(self.containers[container_info.user_id].process.wait)
            container_info = container_info.update(status=False)
            await command_repo.save(container_info)
            if container_info.user_id in self.containers:
                del self.containers[container_info.user_id]
            logger.info(f"Container {container_info.user_id} stopped correctly")
        except Exception as e:
            logger.error(f"Error stopping the container {container_info.user_id}, {e}")

    async def start_acl2_container(self, user_id: str):
        ws_url = f"{settings.WS_PROTOCOL}://{settings.HOST_URL}:{settings.HOST_PORT}/ws/{user_id}"
        try:
            container_info = await command_repo.find_one_by_user_id(user_id, True)
            if self.containers.get(user_id) is not None and container_info is not None:
                output = "ACL2 reloaded from the last session"
                logger.info(f"System reload the container for user {user_id}")
                return CommandResponse(
                    user_id=user_id,
                    output=output,
                    command="",
                    container_id="",
                    ws_url=ws_url
                )
            else:
                container_info = CommandInfo()
                container_name = str(datetime.now().timestamp()).replace(".", "")
                command_list = ["acl2"]
                logger.info(command_list)
                container_instance = CommandInstance(container_name, asyncio.Lock())
                self.containers[user_id] = container_instance
                self.containers[user_id].process = subprocess.Popen(
                    command_list,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=10,
                    shell=True
                )
                output = await self.read_lines_acl2(user_id)
                container_info = container_info.update(status=True, user_id=user_id)
                container_info = await command_repo.save(container_info)
                self.containers[user_id].object_id = container_info.id
                return CommandResponse(
                    user_id=user_id,
                    output=output,
                    command=" ".join(command_list),
                    container_id=container_name,
                    ws_url=ws_url
                )
        except Exception as e:
            error_msg = f"There is an error in 'start_acl2_container'. Error: {e}"
            logger.error(error_msg)
            return CommandResponse(
                user_id=user_id,
                output=error_msg,
                command=" ".join(command_list) if 'command_list' in locals() else "",
                container_id=container_name if 'container_name' in locals() else "",
                ok=False
            )
    
    async def send_command(self, command: str, user_id: str | None) -> CommandResponse:
        output = ""
        ok = True
        try:
            if user_id is not None and (container := self.containers.get(user_id)) is not None:
                logger.info(f"Running command: {command[:50]}")
                async with container.lock:
                    if container.process.poll() is not None:
                        output = "Error: ACL2 session finished."
                    else:
                        msg = command + "\n"
                        logger.info(f"Command sent: {msg}")
                        container.process.stdin.write(msg)
                        container.process.stdin.flush()
                        output = await self.read_lines_acl2(user_id)
                        await self.update_command_info_last_interaction(container.object_id)
            else:
                output = f"The user_id provided: '{user_id}' was null or there are no containers for that user"
                ok = False
        except Exception as e:
            output = f"Error sending command: {e}."
            ok = False
            logger.error(output)
        return CommandResponse(
            user_id=user_id,
            output=output,
            command=command[:50],
            container_id="container_id",
            ok=ok
        )

    
    async def check_solution(self, formula: str, user_id: str):
        output = ""
        ok = True
        container_id = None
        correct = False
        try:
            if user_id is not None and self.containers.get(user_id) is not None:
                container = self.containers[user_id]
                container_id = container.container_id
                logger.info(f"Checking formula: {formula[:50]} in container: {container_id}")
                async with container.lock:
                    if container.process.poll() is not None:
                        output = "Error: ACL2 session finished."
                    else:
                        msg = formula + "\n"
                        logger.info(f"Formula sent {msg}")
                        container.process.stdin.write(msg)
                        container.process.stdin.flush()
                        output = await self.read_lines_acl2(user_id)
                        await self.update_command_info_last_interaction(container.object_id)
                        # Leer una línea extra de forma asíncrona si es necesario
                        _ = await asyncio.to_thread(container.process.stdout.readline)
                        correct = acl2_manager.check_formula(output=output)
            else:
                output = f"The user_id provided: '{user_id}' was null or there are no containers for that user"
                ok = False
        except Exception as e:
            output = f"Error checking solution: {e}."
            ok = False
            logger.error(output)
        return Acl2CheckerResponse(
            container_id=container_id,
            command=formula,
            output=output,
            user_id=user_id,
            correct=correct,
            ok=ok
        )
