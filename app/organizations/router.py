import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.session import get_db
from app.auth.dependencies import get_current_user, check_role
from app.users.models import User
from app.programs.models import Program
from app.applications.models import Application, ApplicationStatusHistory
from app.students.models import StudentProfile
from app.organizations import schemas, service

router = APIRouter(prefix="/organizations", tags=["Organizations"])

# Helper function to generate slug from title
def generate_slug(title: str) -> str:
    import re
    # Remove special characters, lowercase, replace spaces with hyphens
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    # Append short random hash
    return f"{slug}-{str(uuid.uuid4())[:8]}"

@router.post("/register", response_model=schemas.OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def register_organization(
    payload: schemas.OrganizationRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new organization. The account status will be PENDING, and the user
    will have the role 'organization_pending' until approved by an admin.
    """
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las contraseñas no coinciden."
        )

    # Check if email is already registered
    existing_user_query = await db.execute(select(User).where(User.email == payload.contact_email))
    if existing_user_query.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado."
        )

    try:
        org = await service.register_organization(db, payload)
        return org
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al registrar organización: {str(e)}"
        )

@router.get("/me", response_model=schemas.OrganizationResponse)
async def get_my_organization_profile(
    current_user: User = Depends(check_role(["organization"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the organization profile details for the authenticated organization.
    """
    org = await service.get_organization_by_user_id(db, current_user.id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de organización no encontrado."
        )
    return org

@router.put("/me", response_model=schemas.OrganizationResponse)
async def update_my_organization_profile(
    payload: schemas.OrganizationUpdate,
    current_user: User = Depends(check_role(["organization"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates organization profile details.
    """
    org = await service.get_organization_by_user_id(db, current_user.id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de organización no encontrado."
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)

    await db.commit()
    await db.refresh(org)
    return org

@router.get("/me/programs")
async def get_my_programs(
    current_user: User = Depends(check_role(["organization"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the list of opportunities/programs created by this organization.
    """
    org = await service.get_organization_by_user_id(db, current_user.id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de organización no encontrado."
        )
    return await service.get_organization_programs(db, org.id)

@router.post("/me/programs", status_code=status.HTTP_201_CREATED)
async def create_organization_program(
    program_data: dict,
    current_user: User = Depends(check_role(["organization"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new program owned by the authenticated organization.
    """
    org = await service.get_organization_by_user_id(db, current_user.id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de organización no encontrado."
        )

    title = program_data.get("title")
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El título de la convocatoria es requerido."
        )

    slug = generate_slug(title)

    new_prog = Program(
        title=title,
        description=program_data.get("description", ""),
        type=program_data.get("type", "scholarship"),
        organization=org.name,  # Force setting to the organization's name
        organization_name=org.name,
        country=program_data.get("country", "Global"),
        deadline=program_data.get("deadline"),
        eligibility=program_data.get("eligibility", ""),
        benefits=program_data.get("benefits", ""),
        slots=program_data.get("slots"),
        slug=slug,
        is_active=True,
        required_documents=program_data.get("required_documents", []),
        custom_questions=program_data.get("custom_questions", []),
        required_profile_fields=program_data.get("required_profile_fields", []),
        organization_id=org.id  # SECURE: filter-bind by organization_id
    )

    db.add(new_prog)
    await db.commit()
    await db.refresh(new_prog)
    return new_prog

@router.get("/me/applicants", response_model=List[schemas.OrganizationApplicantResponse])
async def get_my_applicants(
    current_user: User = Depends(check_role(["organization"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns candidate applications that applied to opportunities owned by this organization.
    Secured to prevent access to global students list.
    """
    org = await service.get_organization_by_user_id(db, current_user.id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de organización no encontrado."
        )
    
    return await service.get_organization_applicants(db, org.id)

@router.patch("/me/applications/{id}/status")
async def update_applicant_status(
    id: int,
    payload: dict,
    current_user: User = Depends(check_role(["organization"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Update status of an application for a program owned by this organization.
    Records transition in ApplicationStatusHistory and sends notifications.
    """
    org = await service.get_organization_by_user_id(db, current_user.id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de organización no encontrado."
        )

    # Fetch application and check ownership
    result = await db.execute(
        select(Application, Program, StudentProfile, User)
        .join(Program, Application.program_id == Program.id)
        .join(StudentProfile, Application.student_profile_id == StudentProfile.id)
        .join(User, StudentProfile.user_id == User.id)
        .where(Application.id == id, Program.organization_id == org.id)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Postulación no encontrada o no pertenece a tu organización."
        )

    app_record, program, student_profile, student_user = row

    new_status = payload.get("status")
    allowed_statuses = ["PENDING", "IN_REVIEW", "INTERVIEW", "PRESELECTED", "ACCEPTED", "REJECTED", "WITHDRAWN"]
    if not new_status or new_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estado inválido. Estados permitidos: {', '.join(allowed_statuses)}"
        )

    old_status = app_record.status
    app_record.status = new_status
    app_record.applied_at = func.now() if (new_status == "PENDING" and not app_record.applied_at) else app_record.applied_at

    # Insert audit history
    history_rec = ApplicationStatusHistory(
        application_id=app_record.id,
        old_status=old_status,
        new_status=new_status,
        changed_by=current_user.id
    )
    db.add(history_rec)
    await db.commit()
    await db.refresh(app_record)

    # Trigger notifications automatically
    from app.common.notifications import MockEmailService
    try:
        MockEmailService.send_application_status_update_email(
            email=student_user.email,
            student_name=student_user.full_name or "Postulante",
            program_title=program.title,
            new_status=new_status
        )
    except Exception as e:
        import logging
        logger = logging.getLogger("uvicorn.error")
        logger.error(f"Failed to send application status email notification: {e}")

    return {
        "id": app_record.id,
        "status": app_record.status,
        "old_status": old_status
    }

# ================= ADMIN ROUTES =================

# Setup Admin Router with "/admin" prefix but still registered inside organizations module.
# To match user requested routes:
# GET /api/v1/admin/organizations/pending
# PATCH /api/v1/admin/organizations/{id}/approve
# PATCH /api/v1/admin/organizations/{id}/reject
admin_router = APIRouter(prefix="/admin/organizations", tags=["Admin Organizations"])

@admin_router.get("/pending", response_model=List[schemas.OrganizationResponse])
async def list_pending_organizations(
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    List all organizations pending admin approval (Admin only).
    """
    return await service.get_pending_organizations(db)

@admin_router.patch("/{id}/approve", response_model=schemas.OrganizationResponse)
async def approve_org(
    id: int,
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve pending organization (Admin only). Sets status APPROVED and role 'organization'.
    """
    org = await service.approve_organization(db, id, current_user.id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organización no encontrada o falló la aprobación."
        )
    return org

@admin_router.patch("/{id}/reject", response_model=schemas.OrganizationResponse)
async def reject_org(
    id: int,
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Reject pending organization (Admin only). Sets status REJECTED.
    """
    org = await service.reject_organization(db, id, current_user.id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organización no encontrada o falló el rechazo."
        )
    return org
