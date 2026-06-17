import uuid
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from firebase_admin import auth as firebase_auth

from app.core.config import settings
from app.users.models import User
from app.organizations.models import Organization
from app.organizations.schemas import OrganizationRegister, OrganizationUpdate
from app.common.notifications import MockEmailService
from app.programs.models import Program
from app.applications.models import Application
from app.students.models import StudentProfile

async def register_organization(db: AsyncSession, org_in: OrganizationRegister) -> Organization:
    """
    Creates a user in Firebase (with organization_pending claim),
    creates a local User with 'organization_pending' role,
    creates the Organization profile in the local DB with 'PENDING' status,
    and sends a confirmation email.
    """
    email = org_in.contact_email
    name = org_in.contact_name
    password = org_in.password

    # 1. Create Firebase User
    firebase_uid = None
    if settings.MOCK_FIREBASE_AUTH or not settings.FIREBASE_CREDENTIALS_PATH:
        # Development bypass
        firebase_uid = f"mock-org-uid-{uuid.uuid4()}"
    else:
        try:
            fb_user = firebase_auth.create_user(
                email=email,
                password=password,
                display_name=name
            )
            firebase_uid = fb_user.uid
            # Set initial role to organization_pending in Firebase claims
            firebase_auth.set_custom_user_claims(firebase_uid, {"role": "organization_pending"})
        except Exception as e:
            raise RuntimeError(f"Error creating Firebase user: {str(e)}")

    # 2. Create local User record with role organization_pending
    db_user = User(
        firebase_uid=firebase_uid,
        email=email,
        full_name=name,
        role="organization_pending",
        status="active"
    )
    db.add(db_user)
    await db.flush()  # Generate user ID for ForeignKey reference

    # 3. Create local Organization profile
    db_org = Organization(
        user_id=db_user.id,
        name=org_in.name,
        type=org_in.type,
        country=org_in.country,
        city=org_in.city,
        website=org_in.website,
        social_links=org_in.social_links,
        description=org_in.description,
        logo_url=org_in.logo_url,
        contact_name=org_in.contact_name,
        contact_position=org_in.contact_position,
        contact_email=org_in.contact_email,
        contact_phone=org_in.contact_phone,
        verification_document_url=org_in.verification_document_url,
        status="PENDING"
    )
    db.add(db_org)
    await db.commit()
    await db.refresh(db_org)

    # 4. Trigger Email Notification
    try:
        MockEmailService.send_registration_under_review_email(email, org_in.name)
    except Exception as e:
        # Log email sending failure but don't crash the registration transaction
        import logging
        logger = logging.getLogger("uvicorn.error")
        logger.error(f"Failed to send email notification: {e}")

    return db_org

async def get_organization_by_user_id(db: AsyncSession, user_id: int) -> Optional[Organization]:
    """
    Retrieve organization profile by the user ID.
    """
    result = await db.execute(select(Organization).where(Organization.user_id == user_id))
    return result.scalars().first()

async def get_pending_organizations(db: AsyncSession) -> List[Organization]:
    """
    Retrieve all pending organizations.
    """
    result = await db.execute(
        select(Organization).where(Organization.status == "PENDING").order_by(Organization.created_at.desc())
    )
    return result.scalars().all()

async def get_all_organizations(db: AsyncSession, status: Optional[str] = None) -> List[Organization]:
    """
    Retrieve all organizations, optionally filtered by status (PENDING, APPROVED, REJECTED).
    """
    query = select(Organization)
    if status:
        query = query.where(Organization.status == status)
    query = query.order_by(Organization.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

async def approve_organization(db: AsyncSession, org_id: int, admin_user_id: int) -> Optional[Organization]:
    """
    Approves organization: status APPROVED, updates claims to 'organization', User.role to 'organization'.
    """
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    db_org = result.scalars().first()
    if not db_org:
        return None

    # Get user
    user_result = await db.execute(select(User).where(User.id == db_org.user_id))
    db_user = user_result.scalars().first()
    if not db_user:
        return None

    # Update state
    db_org.status = "APPROVED"
    db_org.approved_at = func.now()
    db_org.approved_by = admin_user_id
    
    # Update local role
    db_user.role = "organization"

    # Update Firebase user claims if not mock
    if not settings.MOCK_FIREBASE_AUTH and settings.FIREBASE_CREDENTIALS_PATH:
        try:
            firebase_auth.set_custom_user_claims(db_user.firebase_uid, {"role": "organization"})
        except Exception as e:
            # We can log this but still commit, or raise to undo transactions.
            # Best practice is to raise since auth consistency is vital.
            raise RuntimeError(f"Failed to update Firebase custom claims: {e}")

    await db.commit()
    await db.refresh(db_org)

    # Trigger approved notification email
    MockEmailService.send_organization_approved_email(db_org.contact_email, db_org.name)

    return db_org

async def reject_organization(db: AsyncSession, org_id: int, admin_user_id: int) -> Optional[Organization]:
    """
    Rejects organization: status REJECTED, keeps role organization_pending.
    """
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    db_org = result.scalars().first()
    if not db_org:
        return None

    # Get user
    user_result = await db.execute(select(User).where(User.id == db_org.user_id))
    db_user = user_result.scalars().first()
    if not db_user:
        return None

    # Update state
    db_org.status = "REJECTED"
    db_org.approved_at = None
    db_org.approved_by = admin_user_id
    
    # Keep local role as organization_pending
    db_user.role = "organization_pending"

    # Keeps Firebase claim as organization_pending
    if not settings.MOCK_FIREBASE_AUTH and settings.FIREBASE_CREDENTIALS_PATH:
        try:
            firebase_auth.set_custom_user_claims(db_user.firebase_uid, {"role": "organization_pending"})
        except Exception as e:
            raise RuntimeError(f"Failed to reset Firebase custom claims: {e}")

    await db.commit()
    await db.refresh(db_org)

    # Trigger rejected notification email
    MockEmailService.send_organization_rejected_email(db_org.contact_email, db_org.name)

    return db_org

async def get_organization_programs(db: AsyncSession, org_id: int) -> List[Program]:
    """
    Returns programs created by/associated with this organization.
    """
    result = await db.execute(
        select(Program).where(Program.organization_id == org_id).order_by(Program.id)
    )
    return result.scalars().all()

async def get_organization_applicants(db: AsyncSession, org_id: int) -> List[dict]:
    """
    Returns application details and student details for students applying to programs owned by this organization.
    """
    from sqlalchemy.orm import selectinload
    # Restrict and query candidates securely
    query = (
        select(Application, Program, StudentProfile, User)
        .options(selectinload(Application.status_history))
        .join(Program, Application.program_id == Program.id)
        .join(StudentProfile, Application.student_profile_id == StudentProfile.id)
        .join(User, StudentProfile.user_id == User.id)
        .where(Program.organization_id == org_id)
        .order_by(Application.created_at.desc())
    )
    
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
            "applied_at": app.applied_at,
            "created_at": app.created_at,
            "answers": app.answers or [],
            "uploaded_documents": app.uploaded_documents or {},
            "status_history": history_list,
            "program_title": prog.title,
            "program_slug": prog.slug,
            "student_name": user.full_name or profile.current_institution or "Postulante",
            "student_email": user.email,
            "student_phone": profile.phone,
            "student_country": profile.country,
            "student_city": profile.city,
            "student_education_level": profile.education_level,
            "student_current_institution": profile.current_institution,
            "student_cv_url": profile.cv_url,
            "student_bio": profile.bio,
            "student_birth_date": profile.birth_date,
            "student_area": profile.area,
            "student_english_level": profile.english_level,
            "student_other_languages": profile.other_languages,
            "student_expected_graduation_date": profile.expected_graduation_date,
            "student_work_experience": profile.work_experience,
            "student_volunteer_experience": profile.volunteer_experience,
            "student_general_motivation_letter": profile.general_motivation_letter,
            "student_linkedin_url": profile.linkedin_url,
            "student_portfolio_url": profile.portfolio_url
        })
    return applicants
