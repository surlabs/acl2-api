import docker
import logging
from core.config import settings
from datetime import datetime
from .models.models import ContainerInfo, CommandResponse, Acl2CheckerResponse
from .models.structures import ContainerInstance
from api.websocket_manager import ws_manager
from .repository.container_repo import container_repo
from .acl2_manager import Acl2Manager
import asyncio
from core.logger import logger


acl2_manager = Acl2Manager()

class DockerContainerManagerSdk:
    
    acl2_end = "ACL2 !>"

    def __init__(self):
        self.docker_client = docker.from_env()
        self.acl2_image = settings.ACL2_CONTAINER_NAME
        self.containers: dict[str, ContainerInstance] = {}

    async def start_acl2_container(self, user_id: str):
        """Inicia un contenedor ACL2 para el usuario o reutiliza uno existente."""
        ws_url = f"{settings.WS_PROTOCOL}://{settings.HOST_URL}:{settings.HOST_PORT}/ws/{user_id}"
        
        try:
            # Buscar si el contenedor ya existe
            if user_id in self.containers:
                container_id = self.containers[user_id].container_id
                logger.info(f"Reusing existing container for user {user_id} (Container ID: {container_id})")
                return CommandResponse(user_id=user_id, output="ACL2 session resumed", command="", container_id=container_id, ws_url=ws_url)

            container_name = f"acl2_{user_id}_{int(datetime.now().timestamp())}"
            
            logger.info(f"Starting ACL2 container for user {user_id}")
            container = self.docker_client.containers.run(
                self.acl2_image, 
                command="acl2",
                name=container_name,
                detach=True,
                tty=True,
                stdin_open=True
            )

            self.containers[user_id] = ContainerInstance(container.id, None)
            logger.info(f"Container {container_name} started successfully")

            # Guardar info en BD
            container_info = ContainerInfo().update(status=True, container_id=container.id, user_id=user_id)
            container_info = await container_repo.save(container_info)
            self.containers[user_id].object_id = container_info.id

            return CommandResponse(user_id=user_id, output="ACL2 started", command="", container_id=container.id, ws_url=ws_url)

        except docker.errors.DockerException as e:
            logger.error(f"Error starting ACL2 container: {str(e)}")
            return CommandResponse(user_id=user_id, output=f"Error starting ACL2 container: {str(e)}", command="", container_id=None, ok=False)

    async def send_command(self, command: str, user_id: str):
        """Envía un comando a la sesión activa de ACL2 en el contenedor del usuario."""
        if user_id not in self.containers:
            return CommandResponse(user_id=user_id, output="No active ACL2 session", command=command, container_id=None, ok=False)
        
        container_id = self.containers[user_id].container_id
        container = self.docker_client.containers.get(container_id)

        try:
            logger.info(f"Executing command in container {container_id}: {command}")

            # Ejecutar el comando en la sesión interactiva
            exec_id = self.docker_client.api.exec_create(
                container_id, 
                cmd=f"echo \"{command}\" >> /dev/pts/0",  # Envía el comando a la sesión interactiva de ACL2
                tty=True
            )
            self.docker_client.api.exec_start(exec_id)

            # Leer la respuesta de ACL2
            output = self._read_container_output(container_id)
            
            await ws_manager.send_message(user_id=user_id, message=output)

            return CommandResponse(user_id=user_id, output=output, command=command, container_id=container_id, ok=True)

        except docker.errors.APIError as e:
            logger.error(f"Error sending command to ACL2: {str(e)}")
            return CommandResponse(user_id=user_id, output=f"Error executing command: {str(e)}", command=command, container_id=container_id, ok=False)

    def _read_container_output(self, container_id: str) -> str:
        """Lee la salida actual de ACL2 desde el contenedor."""
        try:
            container = self.docker_client.containers.get(container_id)
            log_output = container.logs(stdout=True, stderr=False, tail=10).decode(errors="replace").strip()

            # Filtrar el prompt ACL2 !>
            output_lines = log_output.split("\n")
            filtered_output = "\n".join([line for line in output_lines if not line.endswith(self.acl2_end)])

            return filtered_output
        except docker.errors.APIError as e:
            logger.error(f"Error reading output from container {container_id}: {str(e)}")
            return "Error reading ACL2 output."

    async def stop_container(self, user_id: str):
        """Detiene y elimina el contenedor ACL2 de un usuario."""
        if user_id not in self.containers:
            return {"error": "No active container found for user"}

        container_id = self.containers[user_id].container_id

        try:
            container = self.docker_client.containers.get(container_id)
            container.stop()
            container.remove()

            del self.containers[user_id]
            logger.info(f"Container {container_id} stopped and removed.")

            return {"message": f"Container {container_id} stopped."}

        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found. Possibly already stopped.")
            return {"error": f"Container {container_id} not found."}

        except docker.errors.APIError as e:
            logger.error(f"Error stopping container: {str(e)}")
            return {"error": f"Error stopping container: {str(e)}"}

    async def check_solution(self, formula: str, user_id: str):
        """Verifica la solución enviada a ACL2."""
        response = await self.send_command(formula, user_id)

        if response.ok:
            correct = acl2_manager.check_formula(output=response.output)
        else:
            correct = False

        return Acl2CheckerResponse(
            container_id=response.container_id, 
            command=formula, 
            output=response.output, 
            user_id=user_id, 
            correct=correct, 
            ok=response.ok
        )
