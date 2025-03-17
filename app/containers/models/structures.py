import subprocess
import threading
from docker.models.containers import Container

class ContainerInstance:
    proccess: subprocess.Popen
    container_id: str
    object_id: str
    lock: threading

    def __init__(self, container_id: str, lock: threading):
        self.container_id = container_id
        self.lock = lock
        self.proccess = None


class DockerInstance:
    docker: Container
    container_id: str
    object_id: str

    def __init__(self, container_id: str):
        self.container_id = container_id
        self.docker = None