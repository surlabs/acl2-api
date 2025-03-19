import pexpect
from core.config import settings
from core.logger import logger
from datetime import datetime
from .models.models import ContainerInfo, CommandResponse, Acl2CheckerResponse
from .models.structures import ContainerInstance
import threading
from api.websocket_manager import ws_manager
from .repository.container_repo import container_repo
from .acl2_manager import Acl2Manager

acl2_manager = Acl2Manager()

class ContainerManagerSpaw:
    privileged_managers = ["podman"]

    def __init__(self):
        self.acl2_image = settings.ACL2_CONTAINER_NAME
        self.containers: dict[str, ContainerInstance] = {}

    async def update_container_info_last_interaction(self, object_id: str) -> None | ContainerInfo:
        res = None
        container_info = await container_repo.find_one(object_id)
        if container_info:
            container_info = container_info.update()
            res = await container_repo.save(container_info)
        else:
            logger.error(f"Container not found: {object_id}")
        return res

    async def read_lines_acl2(self, user_id: str):
        try:
            process = self.containers[user_id].process
            
            output = process.before.strip()  # Captura todo lo que salió antes del prompt
            process.expect_exact("ACL2 !>")  # Esperar hasta que ACL2 muestre su prompt
            logger.info(f"--output--{output}")
            await ws_manager.send_message(user_id=user_id, message=output)
            return output
        except Exception as e:
            logger.error(f"Error reading ACL2 output: {e}")
            return ""

    async def stop_container(self, object_id):
        container_info = await container_repo.find_one(object_id)
        if not container_info:
            logger.error(f"Container {object_id} not found.")
            return

        command = [settings.CONTAINER_MANAGER, "stop", container_info.container_id]
        process = pexpect.spawn(" ".join(command), encoding="utf-8", timeout=5)
        process.expect(pexpect.EOF)

        container_info = container_info.update(status=False)
        await container_repo.save(container_info)

        if container_info.user_id in self.containers:
            del self.containers[container_info.user_id]
        logger.info(f"Container {container_info.container_id} stopped correctly")

    async def start_acl2_container(self, user_id: str):
        ws_url = f"{settings.WS_PROTOCOL}://{settings.HOST_URL}:{settings.HOST_PORT}/ws/{user_id}"
        try:
            container_info = await container_repo.find_one_by_user_id(user_id, True)
            if user_id in self.containers and container_info:
                output = "ACL2 reloaded from the last session"
                logger.info(f"System reload the container for user {user_id}")
                return CommandResponse(user_id=user_id, output=output, command="", container_id=container_info.container_id, ws_url=ws_url)

            container_info = ContainerInfo()
            container_name = str(datetime.now().timestamp()).replace(".", "")
            command = f"{settings.CONTAINER_MANAGER} run --privileged --rm -it --name {container_name} {self.acl2_image} acl2"

            logger.info(command)
            container_instance = ContainerInstance(container_name, threading.Lock())
            self.containers[user_id] = container_instance
            self.containers[user_id].process = pexpect.spawn(command, encoding="utf-8", timeout=None)

            # Esperar a que ACL2 esté listo
            self.containers[user_id].process.expect("ACL2 !>")

            output = await self.read_lines_acl2(user_id)
            container_info = container_info.update(status=True, container_id=container_name, user_id=user_id)
            container_info = await container_repo.save(container_info)

            self.containers[user_id].object_id = container_info.id
            self.containers[user_id].container_id = container_info.container_id

            return CommandResponse(user_id=user_id, output=output, command=command, container_id=container_name, ws_url=ws_url)

        except pexpect.exceptions.ExceptionPexpect as e:
            error_msg = f"Error launching {self.acl2_image} container: {e}"
            logger.error(error_msg)
            return CommandResponse(user_id=user_id, output=error_msg, command=command, container_id=container_name, ok=False)

    async def send_command(self, command: str, user_id: str | None) -> str:
        output = ""
        ok = True
        container_id = None
        try:
            if user_id and user_id in self.containers:
                container_id = self.containers[user_id].container_id
                logger.info(f"Running command: {command[:50]} in container: {container_id}")

                with self.containers[user_id].lock:
                    process = self.containers[user_id].process

                    if not process.isalive():
                        output = "Error: ACL2 session finished."
                    else:
                        logger.info(f"Command sent: {command}")
                        process.sendline(command)
                        process.expect("ACL2 !>")  # Esperar el prompt
                        output = await self.read_lines_acl2(user_id)

                        await self.update_container_info_last_interaction(self.containers[user_id].object_id)
            else:
                output = f"The user_id '{user_id}' is invalid or there are no active containers."
                ok = False

        except pexpect.exceptions.ExceptionPexpect as e:
            output = f"Error sending command: {e}."
            ok = False
            logger.error(output)

        return CommandResponse(user_id=user_id, output=output, command=command[:50], container_id=container_id, ok=ok)

    async def check_solution(self, formula: str, user_id: str):
        output = ""
        ok = True
        container_id = None
        correct = False
        try:
            if user_id and user_id in self.containers:
                container_id = self.containers[user_id].container_id
                logger.info(f"Checking formula: {formula[:50]} in container: {container_id}")

                with self.containers[user_id].lock:
                    process = self.containers[user_id].process

                    if not process.isalive():
                        output = "Error: ACL2 session finished."
                    else:
                        logger.info(f"Formula sent: {formula}")
                        process.sendline(formula)
                        process.expect("ACL2 !>")  # Esperar el prompt
                        output = await self.read_lines_acl2(user_id)

                        await self.update_container_info_last_interaction(self.containers[user_id].object_id)
                        correct = acl2_manager.check_formula(output)

            else:
                output = f"The user_id '{user_id}' is invalid or there are no active containers."
                ok = False

        except pexpect.exceptions.ExceptionPexpect as e:
            output = f"Error checking formula: {e}."
            ok = False
            logger.error(output)

        return Acl2CheckerResponse(container_id=container_id, command=formula, output=output, user_id=user_id, correct=correct, ok=ok)
