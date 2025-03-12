import subprocess
from core.config import settings
from core.logger import logger
from datetime import datetime
from .models.container_info import ContainerInfo

class ContainerManager:

    def __init__(self):
        self.acl2_image = settings.ACL2_CONTAINER_NAME

    async def start_acl2_container(self):
        container_info = ContainerInfo()
        try:
            container_name = str(datetime.now().timestamp())
            command = [
            "podman", "run", "--privileged", "--rm", "-d", "-it", "--name", container_name, self.acl2_image
            ]
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            container_info = container_info.update(container_id=result.stdout, status=True)
            logger.info(f"Container recently launched: {container_info.container_id}")
            container_info = await container_info.save()
        except subprocess.CalledProcessError as e:
            logger.error(f"There is an error launching the {self.acl2_image} container. Error: {e}")
        except Exception as e:
            logger.error(f"There is an error in 'start_acl2_container' container. Error: {e}")
        return container_info