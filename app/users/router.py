from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.users import schemas as user_schemas

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=user_schemas.User)
async def get_users_me(current_user: User = Depends(get_current_user)):
    """
    Returns the current authenticated user's local database profile.
    """
    return current_user
