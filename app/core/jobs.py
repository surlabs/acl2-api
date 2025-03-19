from fastapi_utilities import repeat_every
from fastapi import APIRouter
from core.logger import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from pytz import utc
from fastapi import FastAPI
from containers.repository.container_repo import container_repo
from containers.container_manager import ContainerManager
from containers.docker_container_manager import DockerContainerManager
from core.config import settings

router = APIRouter()
scheduler = AsyncIOScheduler(timezone=utc)
manager = ContainerManager()
manager_docker = DockerContainerManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()


@scheduler.scheduled_job('interval', seconds=settings.CRON_STOP_CONTAINERS)
async def fetch_current_time():
    containers_delete = await (container_repo.get_containers_with_no_interactions())
    logger.info(f"Containers to stop: {[i['container_id'] for i in containers_delete]}")
    for i in containers_delete:
        if settings == "podman":
            await manager.stop_container(i["_id"])
        else:
            await manager_docker.stop_container(i["_id"])
        