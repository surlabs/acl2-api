from fastapi import FastAPI
from containers.container_manager import ContainerManager
from api.router import router

container_manager = ContainerManager()

app = FastAPI(
    title="ACL2 Surlabs",
    description="API para acl2 y sus contenedores",
    version="1.0.0"
)

app.include_router(router)

#@app.get("/")
#def root():
#    return {"message": "¡Bienvenido a la API de FastAPI!"}