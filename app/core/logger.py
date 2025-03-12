import logging
from logging.handlers import TimedRotatingFileHandler


log_handler = TimedRotatingFileHandler(
    "logs/app.log",   # Ruta del archivo de log
    when="midnight",  # Rotar cada medianoche
    interval=1,       # Cada 1 día
    backupCount=7,    # Guardar los últimos 7 días de logs
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

#logger = logging.getLogger("FastAPI")