from pydantic_settings  import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    DEBUG: bool = False  
    DATABASE_NAME: str
    ACL2_CONTAINER_NAME: str
    HOST_URL: str
    HOST_PORT: str
    CONTAINER_VALID_PERIOD_IN_SECONDS: int
    CRON_STOP_CONTAINERS: int
    CONTAINER_MANAGER: str

    class Config:
        env_file = ".env" 
        env_file_encoding = "utf-8"

settings = Settings()