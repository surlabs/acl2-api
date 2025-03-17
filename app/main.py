from fastapi import FastAPI
from containers.container_manager import ContainerManager
from fastapi.middleware.cors import CORSMiddleware
from api.router import router
from core.jobs import lifespan

container_manager = ContainerManager()


app = FastAPI(
    title="ACL2 Surlabs",
    description="API para acl2 y sus contenedores",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las conexiones
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)