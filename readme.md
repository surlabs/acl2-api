## Run MongoDb with composer

### Postman

```bash
podman machine init
podman machine start
podman-composer -d .
```

### Docker

```bash
docker composer up -d
```

## Install all the dependences

```bash
pip install -r requirements
```

## Run the proyect with dev mode

```bash
fastapi dev main.py
```

## Run the proyect with prod mode

```bash
fastapi run
```

### Endpoints

You can access to a swagger endopint. If you deploy the project access to <HOST>/docs