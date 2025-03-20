import logging
from logging.handlers import TimedRotatingFileHandler


log_handler = TimedRotatingFileHandler(
    "/app/app/logs/app.log",  
    when="midnight", 
    interval=1,      
    backupCount=7,   
    encoding="utf-8"
)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler.setFormatter(formatter)

# Crear el logger
logger = logging.getLogger("FastAPI")
logger.setLevel(logging.INFO)



console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

logger.addHandler(log_handler)
logger.addHandler(console_handler)