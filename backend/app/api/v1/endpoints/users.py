from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from app.api import deps
from supabase import Client

router = APIRouter()

@router.get("/", response_model=Any)
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Client = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_admin),
):
    """
    Retrieve users.
    """
    # The Service Role Key allows access to auth.admin methods.
    # Since this is an Admin API, we likely assume the backend runs with SERVICE_ROLE_KEY
    # OR the RLS policies allow admins to see everything.
    # For now, let's assume we query user_profiles which admins can see.
    response = db.table("user_profiles").select("*").range(skip, skip + limit - 1).execute()
    return response.data

@router.get("/{user_id}", response_model=Any)
def read_user(
    user_id: str,
    db: Client = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_admin),
):
    """
    Get a specific user by id.
    """
    response = db.table("user_profiles").select("*").eq("id", user_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")
    return response.data

@router.post("/{user_id}/ban", response_model=Any)
def ban_user(
    user_id: str,
    db: Client = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_admin),
):
    """
    Ban a user.
    """
    response = db.table("user_profiles").update({"status": "banned"}).eq("id", user_id).execute()
    return {"message": "User banned successfully", "user_id": user_id}

@router.post("/{user_id}/unban", response_model=Any)
def unban_user(
    user_id: str,
    db: Client = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_admin),
):
    """
    Unban a user.
    """
    response = db.table("user_profiles").update({"status": "active"}).eq("id", user_id).execute()
    return {"message": "User unbanned successfully", "user_id": user_id}
