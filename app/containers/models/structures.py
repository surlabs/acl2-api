import subprocess
import threading

class ContainerInstance:
    proccess: subprocess.Popen
    conatiner_id: str
    lock: threading

    def __init__(self, container_id: str, lock: threading):
        self.conatiner_id = container_id
        self.lock = lock
        self.proccess = None