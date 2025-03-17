import subprocess
import threading
from docker.models.containers import Container
import pty

class ContainerInstance:
    proccess: subprocess.Popen
    container_id: str
    object_id: str
    lock: threading
    master_fd: int
    slave_fd: int

    def __init__(self, container_id: str, lock: threading):
        self.container_id = container_id
        self.lock = lock
        self.proccess = None
        self.master_fd, self.slave_fd = pty.openpty()
