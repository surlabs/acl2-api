import subprocess
from core.config import settings
from core.logger import logger
from datetime import datetime
from .models.models import ContainerInfo, CommandResponse
from .models.structures import ContainerInstance
import threading

class ContainerManager:

    def __init__(self):
        self.acl2_image = settings.ACL2_CONTAINER_NAME
        self.containers: dict[str,ContainerInstance] = {}

    def read_lines_acl2(self, user_id):
        output = []
        while True:
            line = self.containers[user_id].proccess.stdout.readline().strip()
            if line == "ACL2 !>":  
                break
            output.append(line)
        return "\n".join(output)  

    async def start_acl2_container(self, user_id):
        res = None
        container_info = ContainerInfo()
        try:
            container_name = str(datetime.now().timestamp())
            command = [
            "podman", "run", "--privileged", "--rm", "-it", "--name", container_name, self.acl2_image, "acl2"
            ]

            container_instance = ContainerInstance(container_name, threading.Lock())
            self.containers[user_id] = container_instance
            self.containers[user_id].proccess = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            output = self.read_lines_acl2(user_id)
            container_info = container_info.update(status=True, container_id=container_name, user_id=user_id)
            container_info = await container_info.save()
            res = CommandResponse(user_id=user_id, output=output, command=" ".join(command), container_id=container_name)
        except subprocess.CalledProcessError as e:
            error_msg = f"There is an error launching the {self.acl2_image} container. Error: {e}"
            logger.error(error_msg)
            res = CommandResponse(user_id=user_id, output=error_msg, command=" ".join(command), container_id=container_name, ok=False)
        except Exception as e:
            error_msg = f"There is an error in 'start_acl2_container' container. Error: {e}"
            logger.error(error_msg)
            res = CommandResponse(user_id=user_id, output=error_msg, command=" ".join(command), container_id=container_name, ok=False)
        return res
    

    def send_command(self, command: str, user_id: str | None) -> str:
        output = ""
        ok = True
        container_id = None
        try:
            if user_id is not None and self.containers.get(user_id) is not None:
                container_id = self.containers[user_id].conatiner_id
                logger.info(f"Running the command: {command} in container: {container_id}")
                with self.containers[user_id].lock:
                    if self.containers[user_id].proccess.poll() is not None:
                        output = "Error: ACL2 session finished."
                    else:
                        msg = command + "\n"
                        logger.info(f"Command sended {msg}")
                        self.containers[user_id].proccess.stdin.write(msg) 
                        self.containers[user_id].proccess.stdin.flush()  
                        output = self.read_lines_acl2(user_id)
                        self.containers[user_id].proccess.stdout.readline().strip()
            else:
                output = f"The user_id provided: '{user_id}' was null or there are no containers for that user"
                ok = False
        except Exception as e:
            output = f"Error sending command: {e}."
            ok = False
            logger.error(output)
        return CommandResponse(user_id=user_id, output=output, command=command[:50], container_id=container_id, ok=ok)  
    