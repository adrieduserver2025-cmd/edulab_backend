import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database.session import get_db
from app.applications.models import Application, ApplicationStatusHistory
from app.students.models import StudentProfile
from app.programs.models import Program
from app.users.models import User
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.get("/")
async def get_my_applications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns the authenticated user's applications with program details.
    """
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalars().first()
    if not profile:
        return []
        
    result = await db.execute(
        select(Application, Program)
        .join(Program, Application.program_id == Program.id)
        .where(Application.student_profile_id == profile.id)
    )
    rows = result.all()
    return [
        {
            "id": a.id,
            "student_profile_id": a.student_profile_id,
            "program_id": a.program_id,
            "status": a.status,
            "applied_at": a.applied_at.isoformat() if a.applied_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            "program_title": p.title,
            "program_slug": p.slug,
            "program_type": p.type,
            "program_organization": p.organization
        }
        for a, p in rows
    ]

from typing import Dict, Any

class ApplicationCreate(BaseModel):
    program_id: int
    answers: Optional[list] = None
    uploaded_documents: Optional[dict] = None

@router.post("/", status_code=status.HTTP_201_CREATED)
async def start_application(
    payload: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits or updates an application for a program/opportunity. 
    Saves answers, uploaded documents, sets state to PENDING and registers status history.
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

    # Load program requirements
    program_result = await db.execute(
        select(Program).where(Program.id == payload.program_id)
    )
    program = program_result.scalars().first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programa/Oportunidad no encontrado."
        )

    # Validate profile fields
    req_profile_fields = program.required_profile_fields or []
    missing_fields = []
    for field in req_profile_fields:
        db_field = field
        if field == "cv":
            db_field = "cv_url"
        elif field == "university":
            db_field = "current_institution"
        elif field == "major":
            db_field = "area"
        elif field == "languages":
            db_field = "english_level"
            
        val = getattr(profile, db_field, None)
        if not val or (isinstance(val, str) and not val.strip()):
            missing_fields.append(field)
    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Falta completar los siguientes campos obligatorios del Perfil EDULAB: {', '.join(missing_fields)}"
        )

    # Validate required custom questions
    custom_qs = program.custom_questions or []
    answers_dict = {a.get("question_id"): a.get("answer") for a in (payload.answers or [])}
    missing_qs = []
    for q in custom_qs:
        if q.get("required"):
            ans = answers_dict.get(q.get("id"))
            if not ans or (isinstance(ans, str) and not ans.strip()):
                missing_qs.append(q.get("text"))
    if missing_qs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Debes responder a las siguientes preguntas obligatorias: {', '.join(missing_qs)}"
        )

    # Validate required documents uploaded
    req_docs = program.required_documents or []
    uploaded_docs = payload.uploaded_documents or {}
    missing_docs = []
    for doc in req_docs:
        url = uploaded_docs.get(doc)
        if not url or (isinstance(url, str) and not url.strip()):
            missing_docs.append(doc.upper())
    if missing_docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Falta subir los siguientes documentos obligatorios: {', '.join(missing_docs)}"
        )

    # 2. Check if application already exists
    app_result = await db.execute(
        select(Application).where(
            Application.student_profile_id == profile.id,
            Application.program_id == payload.program_id
        )
    )
    app_record = app_result.scalars().first()

    now_time = datetime.datetime.now(datetime.timezone.utc)

    if app_record:
        old_status = app_record.status
        app_record.status = "PENDING"
        app_record.answers = payload.answers
        app_record.uploaded_documents = payload.uploaded_documents
        app_record.applied_at = now_time

        # Audit History
        history_rec = ApplicationStatusHistory(
            application_id=app_record.id,
            old_status=old_status,
            new_status="PENDING",
            changed_by=current_user.id
        )
        db.add(history_rec)
        await db.commit()
        await db.refresh(app_record)
        return app_record

    # 3. Create new application
    new_app = Application(
        student_profile_id=profile.id,
        program_id=payload.program_id,
        status="PENDING",
        applied_at=now_time,
        motivation_letter_draft=None,
        ai_review_feedback=None,
        answers=payload.answers,
        uploaded_documents=payload.uploaded_documents
    )
    db.add(new_app)
    await db.flush()

    # Initial history record
    initial_history = ApplicationStatusHistory(
        application_id=new_app.id,
        old_status=None,
        new_status="PENDING",
        changed_by=current_user.id
    )
    db.add(initial_history)
    await db.commit()
    await db.refresh(new_app)
    return new_app

@router.post("/{id}/withdraw")
async def withdraw_application(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Allows a student to withdraw their own application. 
    Transition status to WITHDRAWN and logs to audit history.
    """
    # Get student profile
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalars().first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de estudiante no encontrado."
        )

    # Get application
    app_result = await db.execute(
        select(Application, Program).join(Program, Application.program_id == Program.id).where(
            Application.id == id,
            Application.student_profile_id == profile.id
        )
    )
    row = app_result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Postulación no encontrada."
        )

    app_record, program = row
    old_status = app_record.status
    app_record.status = "WITHDRAWN"

    # Insert status history
    history_rec = ApplicationStatusHistory(
        application_id=app_record.id,
        old_status=old_status,
        new_status="WITHDRAWN",
        changed_by=current_user.id
    )
    db.add(history_rec)
    await db.commit()
    await db.refresh(app_record)

    # Mock notify organization of withdrawal
    import logging
    logger = logging.getLogger("uvicorn.error")
    logger.info(f"🔔 NOTIFICACIÓN INTERNA EDULAB: Estudiante {current_user.full_name or 'Estudiante'} retiró su postulación del programa '{program.title}'.")

    return app_record
