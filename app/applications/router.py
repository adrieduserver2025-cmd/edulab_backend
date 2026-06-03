import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database.session import get_db
from app.applications.models import Application
from app.students.models import StudentProfile
from app.users.models import User
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.get("/")
async def get_my_applications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns the authenticated user's applications.
    """
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalars().first()
    if not profile:
        return []
        
    result = await db.execute(
        select(Application).where(Application.student_profile_id == profile.id)
    )
    apps = result.scalars().all()
    return [
        {
            "id": a.id,
            "student_profile_id": a.student_profile_id,
            "program_id": a.program_id,
            "status": a.status,
            "applied_at": a.applied_at.isoformat() if a.applied_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None
        }
        for a in apps
    ]

class ApplicationCreate(BaseModel):
    program_id: int

@router.post("/", status_code=status.HTTP_201_CREATED)
async def start_application(
    payload: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Starts a postulation for a program/opportunity. If the user doesn't have
    a StudentProfile, a stub/minimal profile is created automatically to satisfy constraints.
    """
    # 1. Check/Get student profile
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalars().first()

    if not profile:
        # Auto-create minimal stub profile to prevent DB constraints crashes
        profile = StudentProfile(
            user_id=current_user.id,
            country="Bolivia",
            city="Santa Cruz",
            birth_date=datetime.date(2000, 1, 1),
            phone="",
            education_level="Undergraduate",
            current_institution="Universidad Privada",
            area="General",
            english_level="Basic",
            other_languages=[],
            interests=["Volunteering"],
            target_countries=["Brasil"],
            target_program_types=["volunteering"],
            profile_completion=10  # Started stub gets 10%
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    # 2. Check if application already exists
    app_result = await db.execute(
        select(Application).where(
            Application.student_profile_id == profile.id,
            Application.program_id == payload.program_id
        )
    )
    app_record = app_result.scalars().first()

    if app_record:
        return app_record

    # 3. Create new application
    new_app = Application(
        student_profile_id=profile.id,
        program_id=payload.program_id,
        status="started",
        applied_at=None,
        motivation_letter_draft=None,
        ai_review_feedback=None
    )
    db.add(new_app)
    await db.commit()
    await db.refresh(new_app)
    return new_app
