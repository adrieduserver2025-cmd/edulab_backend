from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.students.models import StudentProfile
from app.documents.models import Document

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get("/")
async def get_my_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns the authenticated user's documents.
    """
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalars().first()
    if not profile:
        return []
        
    result = await db.execute(
        select(Document).where(Document.student_profile_id == profile.id)
    )
    docs = result.scalars().all()
    return [
        {
            "id": d.id,
            "student_profile_id": d.student_profile_id,
            "name": d.name,
            "type": d.type,
            "file_url": d.file_url,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None
        }
        for d in docs
    ]
