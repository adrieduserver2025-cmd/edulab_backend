from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.users import schemas as user_schemas
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=user_schemas.User)
async def get_users_me(current_user: User = Depends(get_current_user)):
    """
    Returns the current authenticated user's local database profile.
    """
    return current_user

@router.patch("/me", response_model=user_schemas.User)
async def update_user_me(
    user_in: user_schemas.UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current authenticated user's details.
    """
    update_data = user_in.model_dump(exclude_unset=True)
    
    # Do not allow users to elevate their own role or verify themselves maliciously
    if "role" in update_data:
        del update_data["role"]
    if "status" in update_data:
        del update_data["status"]
    if "is_verified" in update_data:
        del update_data["is_verified"]
        
    for field, value in update_data.items():
        setattr(current_user, field, value)
        
    await db.commit()
    await db.refresh(current_user)
    return current_user
