from fastapi_utilities import repeat_every
from fastapi import APIRouter
from core.logger import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from pytz import utc
from fastapi import FastAPI
from containers.repository.command_repo import command_repo
from containers.command_manager import CommandManager

from core.config import settings

router = APIRouter()
scheduler = AsyncIOScheduler(timezone=utc)
manager = CommandManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()


@scheduler.scheduled_job('interval', seconds=settings.CRON_STOP_PROCESS)
async def fetch_current_time():
    process_stop = await (command_repo.get_commands_with_no_interactions())
    logger.info(f"Process to stop: {[i['_id'] for i in process_stop]}")
    for i in process_stop:
        await manager.stop_process(i["_id"])
       
        