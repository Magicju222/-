from typing import Any, List
from fastapi import APIRouter, Depends
from backend.app.api import deps
from supabase import Client

router = APIRouter()

@router.get("/", response_model=Any)
def read_logs(
    skip: int = 0,
    limit: int = 100,
    db: Client = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_admin),
):
    """
    Retrieve cleaning logs (Admin only).
    """
    response = db.table("cleaning_logs").select("*").order("created_at", desc=True).range(skip, skip + limit - 1).execute()
    return response.data

@router.get("/stats", response_model=Any)
def read_stats(
    db: Client = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_admin),
):
    """
    Get simple stats.
    """
    # Note: Supabase-py doesn't support 'count' easily in select without returning data sometimes, 
    # or we use 'head=True, count="exact"'.
    
    total_logs = db.table("cleaning_logs").select("*", count="exact", head=True).execute()
    total_users = db.table("user_profiles").select("*", count="exact", head=True).execute()
    
    return {
        "total_cleaning_tasks": total_logs.count,
        "total_users": total_users.count
    }
