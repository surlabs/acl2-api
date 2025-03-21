import subprocess
import threading

class ContainerInstance:
    proccess: subprocess.Popen
    container_id: str
    object_id: str
    lock: threading

    def __init__(self, container_id: str, lock):
        self.container_id = container_id
        self.lock = lock
        self.proccess = None
        
class CommandInstance:
    proccess: subprocess.Popen
    object_id: str
    lock: threading
    secret: str

    def __init__(self, container_id: str, lock, secret: str):
        self.container_id = container_id
        self.proccess = None
        self.lock = lock
        self.secret = secret
