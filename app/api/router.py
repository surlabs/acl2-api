from fastapi import APIRouter
from containers.router import container_router

router = APIRouter(prefix="/V1")

router.include_router(container_router, prefix="/acl2", tags=["acl2"])