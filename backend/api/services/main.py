##### IMPORTS #####

# Third-party Libraries
from fastapi import FastAPI

# Local Imports
from services.routes import (
    console,
    eula,
    properties,
    servers,
    version
)


##### APPLICATION #####
app = FastAPI()

app.include_router(console.router)
app.include_router(eula.router)
app.include_router(properties.router)
app.include_router(servers.router)
app.include_router(version.router)