import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database.session import get_db
from app.applications.models import Application, ApplicationStatusHistory
from app.students.models import StudentProfile
from app.programs.models import Program
from app.users.models import User
from app.auth.dependencies import get_current_user, check_role

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

from typing import Dict, Any, Optional

class ApplicationCreate(BaseModel):
    program_id: int
    status: Optional[str] = "pending"  # started or pending
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

    is_draft = payload.status == "started"

    # Only validate fields if it is not a draft (i.e. status is pending)
    if not is_draft:
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
    target_status = payload.status or "pending"

    if app_record:
        old_status = app_record.status
        app_record.status = target_status
        app_record.answers = payload.answers
        app_record.uploaded_documents = payload.uploaded_documents
        
        # If moving to pending, set applied_at
        if target_status == "pending" and old_status != "pending":
            app_record.applied_at = now_time
        else:
            app_record.applied_at = app_record.applied_at or now_time

        # Audit History only if status actually changed
        if old_status != target_status:
            history_rec = ApplicationStatusHistory(
                application_id=app_record.id,
                old_status=old_status,
                new_status=target_status,
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
        status=target_status,
        applied_at=now_time if target_status == "pending" else None,
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
        new_status=target_status,
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
    Transition status to withdrawn and logs to audit history.
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
    app_record.status = "withdrawn"

    # Insert status history
    history_rec = ApplicationStatusHistory(
        application_id=app_record.id,
        old_status=old_status,
        new_status="withdrawn",
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

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    answers: Optional[list] = None
    uploaded_documents: Optional[dict] = None

@router.get("/admin", response_model=List[dict])
async def list_all_applications_by_admin(
    status: Optional[str] = None,
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    List all candidate applications in the system (Admin only).
    """
    from sqlalchemy.orm import selectinload
    query = (
        select(Application, Program, StudentProfile, User)
        .options(selectinload(Application.status_history))
        .join(Program, Application.program_id == Program.id)
        .join(StudentProfile, Application.student_profile_id == StudentProfile.id)
        .join(User, StudentProfile.user_id == User.id)
        .order_by(Application.created_at.desc())
    )
    if status:
        query = query.where(Application.status == status)
        
    result = await db.execute(query)
    rows = result.all()
    
    applicants = []
    for app, prog, profile, user in rows:
        history_list = []
        if app.status_history:
            for h in app.status_history:
                history_list.append({
                    "id": h.id,
                    "old_status": h.old_status,
                    "new_status": h.new_status,
                    "changed_by": h.changed_by,
                    "created_at": h.created_at
                })
        applicants.append({
            "id": app.id,
            "student_profile_id": app.student_profile_id,
            "program_id": app.program_id,
            "status": app.status,
            "applied_at": app.applied_at.isoformat() if app.applied_at else None,
            "created_at": app.created_at.isoformat() if app.created_at else None,
            "answers": app.answers or [],
            "uploaded_documents": app.uploaded_documents or {},
            "status_history": history_list,
            "program_title": prog.title,
            "program_slug": prog.slug,
            "student_name": user.full_name or "Postulante",
            "student_email": user.email,
            "student_phone": profile.phone,
            "student_country": profile.country,
            "student_city": profile.city,
            "student_education_level": profile.education_level,
            "student_current_institution": profile.current_institution,
            "student_cv_url": profile.cv_url,
            "student_bio": profile.bio,
            "student_birth_date": profile.birth_date.isoformat() if profile.birth_date else None,
            "student_area": profile.area,
            "student_english_level": profile.english_level,
            "student_expected_graduation_date": profile.expected_graduation_date.isoformat() if profile.expected_graduation_date else None,
            "student_linkedin_url": profile.linkedin_url,
            "student_portfolio_url": profile.portfolio_url
        })
    return applicants

@router.put("/{id}")
async def update_application_by_id(
    id: int,
    payload: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates an application status or details. Available to Admin, or status-only update to Organization.
    """
    result = await db.execute(
        select(Application, StudentProfile, Program)
        .join(StudentProfile, Application.student_profile_id == StudentProfile.id)
        .join(Program, Application.program_id == Program.id)
        .where(Application.id == id)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Postulación no encontrada."
        )
        
    app_record, student_profile, program = row
    
    # Check permissions
    is_admin = current_user.role == "admin"
    is_org_owner = False
    if current_user.role == "organization":
        from app.organizations.models import Organization
        org_res = await db.execute(select(Organization).where(Organization.user_id == current_user.id))
        org = org_res.scalars().first()
        if org and program.organization_id == org.id:
            is_org_owner = True
            
    if not (is_admin or is_org_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar esta postulación."
        )

    # Apply updates
    update_data = payload.model_dump(exclude_unset=True)
    
    if "status" in update_data:
        new_status = update_data["status"].lower()
        allowed_statuses = ["started", "pending", "in_review", "accepted", "rejected"]
        if new_status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado inválido. Estados permitidos: {', '.join(allowed_statuses)}"
            )
            
        old_status = app_record.status
        if old_status != new_status:
            app_record.status = new_status
            # Add audit history
            history_rec = ApplicationStatusHistory(
                application_id=app_record.id,
                old_status=old_status,
                new_status=new_status,
                changed_by=current_user.id
            )
            db.add(history_rec)

    if "answers" in update_data and is_admin: # Only admin can modify student answers
        app_record.answers = update_data["answers"]
        
    if "uploaded_documents" in update_data and is_admin: # Only admin can modify uploaded documents
        app_record.uploaded_documents = update_data["uploaded_documents"]

    await db.commit()
    await db.refresh(app_record)
    return app_record

@router.delete("/{id}")
async def delete_application(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Deletes an application by ID. Accessible by Admin, the student who owns it,
    or the organization that owns the program.
    """
    # 1. Fetch application, student profile, program details
    result = await db.execute(
        select(Application, StudentProfile, Program)
        .join(StudentProfile, Application.student_profile_id == StudentProfile.id)
        .join(Program, Application.program_id == Program.id)
        .where(Application.id == id)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Postulación no encontrada."
        )
        
    app_record, student_profile, program = row
    
    # 2. Check permissions
    is_admin = current_user.role == "admin"
    is_student_owner = student_profile.user_id == current_user.id
    
    is_org_owner = False
    if current_user.role == "organization":
        from app.organizations.models import Organization
        org_res = await db.execute(select(Organization).where(Organization.user_id == current_user.id))
        org = org_res.scalars().first()
        if org and program.organization_id == org.id:
            is_org_owner = True
            
    if not (is_admin or is_student_owner or is_org_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar esta postulación."
        )
        
    # 3. Clean up history audit first
    from sqlalchemy import delete
    await db.execute(delete(ApplicationStatusHistory).where(ApplicationStatusHistory.application_id == id))
    
    # 4. Delete the application
    await db.delete(app_record)
    await db.commit()
    return {"detail": "Postulación eliminada con éxito."}
