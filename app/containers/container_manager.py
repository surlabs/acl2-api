import subprocess
from core.config import settings
from core.logger import logger
from datetime import datetime
from .models.models import ContainerInfo, CommandResponse
from .models.structures import ContainerInstance, DockerInstance
import threading
from api.websocket_manager import ws_manager
from .repository.container_repo import container_repo
import docker
import pexpect
from pexpect.popen_spawn import PopenSpawn


class ContainerManager:

    privileged_managers = ["podman"]

    def __init__(self):
        self.acl2_image = settings.ACL2_CONTAINER_NAME
        self.containers: dict[str,ContainerInstance] = {}
        self.dockers: dict[str,DockerInstance] = {}
        self.client = docker.from_env()

    async def update_container_info_last_interaction(self, object_id: str) -> None|ContainerInfo:
        res = None
        container_info = await container_repo.find_one(object_id)
        if container_info is not None:
            container_info = container_info.update()
            res = await container_repo.save(container_info)
            return res
        else:
            logger.error(f"Container not found: {object_id}")

    async def read_lines_acl2(self, user_id: str):
        output = []
        while True:
            line: str = self.containers[user_id].proccess.stdout.readline().strip()
            logger.info(f"--------{line}-------")
            #await ws_manager.send_message(user_id=user_id, message=line)
            if line == "ACL2 !>" or len(line) == 0:  
                break
            output.append(line)
        return "\n".join(output)  
    
    async def stop_container(self, object_id):
        container_info = await container_repo.find_one(object_id)
        command = [
            settings.CONTAINER_MANAGER, "stop", container_info.container_id
        ]
        process = subprocess.run(command, capture_output=True)
        if process.returncode != -1:
            container_info = container_info.update(status=False)
            await container_repo.save(container_info)
            logger.info(f"Container {container_info.container_id} stopped correctly")
        else:
            logger.error(f"Erorr stopping the container {container_info.container_id}")

    async def start_docker(self):
        command = "winpty docker run --rm -it --name 1742201236365 --privileged -it acl2_ubuntu_not_launch acl2"
        child = PopenSpawn(command, encoding='utf-8')

        try:
            # Bucle para leer la salida del proceso
            while True:
                line = child.readline()  # Lee una línea de la salida
                if line:
                    # Aquí puedes procesar la línea o simplemente imprimirla
                    logger.info(line)  # 'end' evita saltos de línea dobles
                else:
                    break
        except pexpect.EOF:
            logger.error("El proceso ha terminado.")
        except KeyboardInterrupt:
            logger.error("Interrumpido por el usuario.")

    async def start_acl2_container(self, user_id):
        res = None
        container_info = ContainerInfo()
        logger.info("-----------------")
        try:
            container_name = str(datetime.now().timestamp()).replace(".","")
            priviliged_argument = "--privileged" if settings.CONTAINER_MANAGER in self.privileged_managers else ""
            if settings.CONTAINER_MANAGER in self.privileged_managers:
                command = [
                    settings.CONTAINER_MANAGER, "run", "--privileged", "--rm", "-it", "--name", container_name, self.acl2_image, "acl2"
                ]
            else:
                command = [
                    settings.CONTAINER_MANAGER, "run", "--rm", "-it", "--name", container_name, "--privileged", self.acl2_image, "acl2"
                ]
            
            command = ["docker", "run", "--privileged",
                "--name", container_name,
                "-it",  # Modo interactivo
                "--rm",  # Para eliminar el contenedor después de que se detenga
                self.acl2_image,
                "bash", "-c", "acl2"
            ]
            
            logger.info(" ".join(command))
            container_instance = ContainerInstance(container_name, threading.Lock())
            self.containers[user_id] = container_instance
            self.containers[user_id].proccess = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,  # Redirigir entrada al PTY
                stdout=subprocess.PIPE,  # Redirigir salida al PTY
                stderr=subprocess.PIPE,  # Capturar errores en el mismo flujo
                text=True,
                bufsize=1
            )
            output = await self.read_lines_acl2(user_id)
            container_info = container_info.update(status=True, container_id=container_name, user_id=user_id)
            logger.info("-------- presave")
            container_info = await container_repo.save(container_info)
            logger.info("-------- postsave")
            self.containers[user_id].object_id = container_info.id
            self.containers[user_id].container_id = container_info.container_id
            ws_url = f"ws://{settings.HOST_URL}:{settings.HOST_PORT}/ws/{user_id}"
            res = CommandResponse(user_id=user_id, output=output, command=" ".join(command), container_id=container_name, ws_url=ws_url)
        except subprocess.CalledProcessError as e:
            error_msg = f"There is an error launching the {self.acl2_image} container. Error: {e}"
            logger.error(error_msg)
            res = CommandResponse(user_id=user_id, output=error_msg, command=" ".join(command), container_id=container_name, ok=False)
        except Exception as e:
            error_msg = f"There is an error in 'start_acl2_container'. Error: {e}"
            logger.error(error_msg)
            res = CommandResponse(user_id=user_id, output=error_msg, command=" ".join(command), container_id=container_name, ok=False)
        return res
    

    async def send_command(self, command: str, user_id: str | None) -> str:
        output = ""
        ok = True
        container_id = None
        try:
            if user_id is not None and self.containers.get(user_id) is not None:
                container_id = self.containers[user_id].container_id
                logger.info(f"Running the command: {command[:50]} in container: {container_id}")
                with self.containers[user_id].lock:
                    if self.containers[user_id].proccess.poll() is not None:
                        output = "Error: ACL2 session finished."
                    else:
                        msg = command + "\n"
                        logger.info(f"Command sent {msg}")
                        self.containers[user_id].proccess.stdin.write(msg) 
                        self.containers[user_id].proccess.stdin.flush()  
                        output = await self.read_lines_acl2(user_id)
                        await self.update_container_info_last_interaction(self.containers[user_id].object_id)
                        self.containers[user_id].proccess.stdout.readline().strip()
            else:
                output = f"The user_id provided: '{user_id}' was null or there are no containers for that user"
                ok = False
        except Exception as e:
            output = f"Error sending command: {e}."
            ok = False
            logger.error(output)
        return CommandResponse(user_id=user_id, output=output, command=command[:50], container_id=container_id, ok=ok)  
    

    async def start_acl2_container_docker(self, user_id: str):
        container_name = str(datetime.now().timestamp())
        container_info = ContainerInfo()
        self.dockers[user_id] = DockerInstance(container_id=container_name)
        self.dockers[user_id].docker = self.client.containers.run(
            self.acl2_image,
            detach=True,
            tty=True,
            auto_remove=True,
            stdin_open=True,
            privileged = True,
            name=container_name,
            stdout=True,
            command="acl2"
        )
        #exec_id, output = self.dockers[user_id].exec_run("acl2")
        container_info = container_info.update(status=True, container_id=container_name, user_id=user_id)
        container_info = await container_repo.save(container_info)
        #await ws_manager.send_message(user_id=user_id, message=output)
        logger.info(self.dockers[user_id].docker)

    async def send_command_docker(self, command: str, user_id: str | None) -> str:
        output = ""
        ok = True
        container_id = None
        try:
            if user_id is not None and self.dockers.get(user_id) is not None:
                docker_container = self.dockers.get(user_id).docker
                logger.info(f"Running the command: {command[:50]} in container: {container_id}")
               
                msg = command + "\n"
                logger.info(f"Command sent {msg}")
                exec_id = self.client.api.exec_create(
                    docker_container.id,
                    cmd=command,
                    tty=True,  # Mantener la terminal activa
                    stdin=True
                )
                output = self.client.api.exec_start(exec_id, tty=True)
                logger.info(output)
                await ws_manager.send_message(user_id=user_id, message=output)
                await self.update_container_info_last_interaction(self.containers[user_id].object_id)
            else:
                output = f"The user_id provided: '{user_id}' was null or there are no containers for that user"
                ok = False
        except Exception as e:
            output = f"Error sending command: {e}."
            ok = False
            logger.error(output)
        return CommandResponse(user_id=user_id, output=output, command=command[:50], container_id=container_id, ok=ok)  