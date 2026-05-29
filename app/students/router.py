from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.students import schemas as student_schemas
from app.students import service as student_service

router = APIRouter(prefix="/student-profile", tags=["Student Profile"])

@router.get("/me", response_model=student_schemas.StudentProfile | None)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the authenticated user's student profile if it exists, or null.
    """
    profile = await student_service.get_profile_by_user_id(db, current_user.id)
    return profile

@router.post("/me", response_model=student_schemas.StudentProfile, status_code=status.HTTP_201_CREATED)
async def create_my_profile(
    profile_in: student_schemas.StudentProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a student profile for the authenticated user.
    Only one profile per user can exist.
    """
    existing_profile = await student_service.get_profile_by_user_id(db, current_user.id)
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student profile already exists for this user."
        )
    profile = await student_service.create_profile(db, profile_in, current_user.id)
    return profile

@router.put("/me", response_model=student_schemas.StudentProfile)
async def update_my_profile(
    profile_in: student_schemas.StudentProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates the student profile for the authenticated user.
    """
    profile = await student_service.update_profile(db, profile_in, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found for this user."
        )
    return profile
