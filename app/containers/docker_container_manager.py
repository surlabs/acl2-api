import subprocess
from core.config import settings
from core.logger import logger
from datetime import datetime
from .models.models import ContainerInfo, CommandResponse, Acl2CheckerResponse
from .models.structures import ContainerInstance
import threading
from api.websocket_manager import ws_manager
from .repository.container_repo import container_repo
import os
from .acl2_manager import Acl2Manager

acl2_manager = Acl2Manager()

class DockerContainerManager:
    
    acl2_end = "'ACL2 !>'"

    def __init__(self):
        self.acl2_image = settings.ACL2_CONTAINER_NAME
        self.containers: dict[str,ContainerInstance] = {}
        
    async def read_container_response(self, user_id: str, first: bool = True) -> str:
        output = []
        logger.info("Start reading container response")

        while True:
            try:
                logger.info("----")
                raw_data = os.read(self.containers[user_id].master_fd, 1024)  # Leer datos en bruto
                if not raw_data:
                    break  # Salir del bucle si no hay más datos
                
                data = raw_data.decode(errors="replace").replace("\r", "").strip()  # Decodificar y limpiar
                logger.info(f"**data**{repr(data)}")
                
                logger.info(f"*** Data loaded: {repr(data)}")  # Usar repr solo en el log
                if repr(data) == "'\x1b[KACL2 !>'":
                    break
                if repr(data).endswith(self.acl2_end) or repr(data).endswith("!>ACL2 !>'"):  # Si la respuesta termina con el prompt de ACL2
                    output.append(data)
                    if first:  # Si es la primera llamada, seguir leyendo
                        first = False
                        continue
                    else:
                        break  # Terminar la lectura si ya es una continuación
                    
                output.append(data)

            except OSError as e:
                logger.error(f"Error reading container response: {str(e)}")
                break  
            except Exception:
                logger.info("exception")
        return " ".join(output)

    async def read_full_output(self, user_id: str):
        output = []
        logger.info("start to read")
        counter = 0
        while True:
            try:
                
                data = repr(os.read(self.containers[user_id].master_fd, 1024).decode())
                logger.info(f"+++data**::::{(data)}*---*")
                
                if data.replace("\r", "").strip().endswith(self.acl2_end):
                    counter += 1
                if data.replace("\r", "").strip().endswith(self.acl2_end) and counter > 2:
                    logger.info(f"Tabulation deleted--{data}--")
                    datat_to_send = data[:data.index(self.acl2_end)+len(self.acl2_end)]
                    output.append(datat_to_send)
                    await ws_manager.send_message(user_id=user_id, message=datat_to_send)
                    logger.info("The fix is into")
                    return "".join(output)
                if not data or data.replace(" ", "") == "":
                    await ws_manager.send_message(user_id=user_id, message=data)
                    logger.info(f"--{data}--")
                    return "".join(output)
                await ws_manager.send_message(user_id=user_id, message=data)
                output.append(data)
            except OSError:
                logger.error("Error decoding the response")
                break  
    
    async def update_container_info_last_interaction(self, object_id: str) -> None|ContainerInfo:
        res = None
        container_info = await container_repo.find_one(object_id)
        if container_info is not None:
            container_info = container_info.update()
            res = await container_repo.save(container_info)
            return res
        else:
            logger.error(f"Container not found: {object_id}")
    
    async def stop_container(self, object_id):
        container_info = await container_repo.find_one(object_id)
        command = [
            settings.CONTAINER_MANAGER, "stop", container_info.container_id
        ]
        process = subprocess.run(command, capture_output=True)
        if process.returncode != -1:
            container_info = container_info.update(status=False)
            await container_repo.save(container_info)
            if container_info.user_id in self.containers:
                del self.containers[container_info.user_id]
            logger.info(f"Container {container_info.container_id} stopped correctly")
        else:
            logger.error(f"Erorr stopping the container {container_info.container_id}")

    async def start_acl2_container(self, user_id: str):
        res = None
        ws_url = f"{settings.WS_PROTOCOL}://{settings.HOST_URL}:{settings.HOST_PORT}/ws/{user_id}"
        try:
            container_info = await container_repo.find_one_by_user_id(user_id, True)
            if self.containers.get(user_id) is not None and container_info is not None:
                output = "ACL2 reloaded from the last session"
                logger.info(f"System reload the container for user {user_id}")
                res = CommandResponse(user_id=user_id, output=output, command="", container_id=container_info.container_id, ws_url=ws_url)
            else: 
                container_info = ContainerInfo()
                container_name = str(datetime.now().timestamp()).replace(".","")
                command = [
                        settings.CONTAINER_MANAGER, "run", "--privileged", "--rm", "-it", "--name", container_name, self.acl2_image, "acl2"
                    ]
                logger.info(" ".join(command))
                container_instance = ContainerInstance(container_name, threading.Lock())
                self.containers[user_id] = container_instance
                self.containers[user_id].proccess = subprocess.Popen(
                    command,
                    stdin=self.containers[user_id].slave_fd,
                    stdout=self.containers[user_id].slave_fd,
                    stderr=self.containers[user_id].slave_fd,
                    text=True,
                    bufsize=1
                )
                output = await self.read_container_response(user_id)
                #os.read(self.containers[user_id].master_fd, 1024).decode()
                logger.info(f"output readen for user {user_id}")
                container_info = container_info.update(status=True, container_id=container_name, user_id=user_id)
                container_info = await container_repo.save(container_info)
                self.containers[user_id].object_id = container_info.id
                self.containers[user_id].container_id = container_info.container_id
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
                logger.info(f"Running the command: {repr(command[:50])} in container: {container_id}")
                with self.containers[user_id].lock:
                    if self.containers[user_id].proccess.poll() is not None:
                        output = "Error: ACL2 session finished."
                    else:
                        msg = command + "\n"
                        logger.info(f"Command sent {repr(msg)}***")
                        os.write(self.containers[user_id].master_fd, msg.encode())
                        output = await self.read_container_response(user_id)
                        await self.update_container_info_last_interaction(self.containers[user_id].object_id)
            else:
                output = f"The user_id provided: '{user_id}' was null or there are no containers for that user"
                ok = False
        except Exception as e:
            output = f"Error sending command: {e}."
            ok = False
            logger.error(output)
        return CommandResponse(user_id=user_id, output=output, command=command[:50], container_id=container_id, ok=ok)  
    
    async def check_solution(self, formula: str, user_id: str):
        output = ""
        ok = True
        container_id = None
        correct: bool = False
        try:
            if user_id is not None and self.containers.get(user_id) is not None:
                container_id = self.containers[user_id].container_id
                logger.info(f"Checking formula: {formula[:50]} in container: {container_id}")
                with self.containers[user_id].lock:
                    if self.containers[user_id].proccess.poll() is not None:
                        output = "Error: ACL2 session finished."
                    else:
                        msg = formula + "\n"
                        logger.info(f"Formula sent {msg}")
                        self.containers[user_id].proccess.stdin.write(msg) 
                        self.containers[user_id].proccess.stdin.flush()  
                        output = await self.read_full_output(user_id)
                        await self.update_container_info_last_interaction(self.containers[user_id].object_id)
                        self.containers[user_id].proccess.stdout.readline().strip()
                        correct = acl2_manager.check_formula(output=output)
            else:
                output = f"The user_id provided: '{user_id}' was null or there are no containers for that user"
                ok = False
        except Exception as e:
            output = f"Error sending command: {e}."
            ok = False
            logger.error(output)
        return Acl2CheckerResponse(container_id=container_id, command=formula, output=output, user_id=user_id, correct=correct, ok=ok)
   