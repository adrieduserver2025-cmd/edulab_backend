from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.users import schemas as user_schemas

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/me", response_model=user_schemas.User)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the current authenticated user's profile and roles.
    """
    return current_user

@router.post("/sync", response_model=user_schemas.User)
async def sync_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Forcefully synchronizes or verifies local DB registration for the authenticated user.
    Called by the frontend immediately after a successful Firebase client authentication.
    Also updates the last_login timestamp.
    """
    current_user.last_login = func.now()
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user
