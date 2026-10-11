from fastapi import FastAPI
from services.app import router

app = FastAPI()

app.include_router(router)