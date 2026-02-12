from typing import Any, Dict
from fastapi import APIRouter, Depends, Body
from app.api import deps
from supabase import Client
from pydantic import BaseModel

router = APIRouter()

class ConfigUpdate(BaseModel):
    key: str
    value: str

@router.get("/", response_model=Any)
def read_config(
    db: Client = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_admin),
):
    """
    Retrieve system config (Admin only).
    """
    response = db.table("system_config").select("*").execute()
    return response.data

@router.put("/", response_model=Any)
def update_config(
    config: ConfigUpdate,
    db: Client = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_admin),
):
    """
    Update a specific config key and return all updated config.
    """
    # Update the specific config key
    db.table("system_config").update({"value": config.value}).eq("key", config.key).execute()

    # Return all config to ensure frontend has latest data
    response = db.table("system_config").select("*").execute()
    return response.data
