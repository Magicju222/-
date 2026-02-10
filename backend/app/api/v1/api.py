from fastapi import APIRouter
from backend.app.api.v1.endpoints import users, logs, config

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(config.router, prefix="/config", tags=["config"])
