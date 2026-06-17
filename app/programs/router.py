from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.programs.models import Program
from app.auth.dependencies import get_current_user, check_role
from app.users.models import User

router = APIRouter(prefix="/programs", tags=["Programs"])

@router.get("/")
async def list_programs(db: AsyncSession = Depends(get_db)):
    """
    List all active approved educational programs (scholarships, leadership, summer schools, etc.).
    """
    result = await db.execute(select(Program).where(Program.is_active == True, Program.status == "approved"))
    programs = result.scalars().all()
    # If DB is empty, return a set of beautiful initial mock data
    if not programs:
        return [
            {
                "id": 1,
                "title": "Beca de Excelencia Global DAAD Alemania",
                "description": "Beca completa para estudios de Master y Doctorado en universidades alemanas.",
                "type": "scholarship",
                "organization": "Servicio Alemán de Intercambio Académico (DAAD)",
                "country": "Alemania",
                "deadline": "2026-10-15",
                "benefits": "Matrícula completa, estipendio mensual de €1200 y seguro médico."
            },
            {
                "id": 2,
                "title": "Summer School en Liderazgo y Sostenibilidad Oxford",
                "description": "Programa intensivo de verano enfocado en políticas ambientales globales.",
                "type": "summer_school",
                "organization": "University of Oxford",
                "country": "Reino Unido",
                "deadline": "2026-06-30",
                "benefits": "Alojamiento, alimentación y pase de biblioteca."
            },
            {
                "id": 3,
                "title": "Intercambio Académico Global U-Tokyo",
                "description": "Semestre académico en ingeniería o ciencias computacionales.",
                "type": "exchange",
                "organization": "University of Tokyo",
                "country": "Japón",
                "deadline": "2026-08-01",
                "benefits": "Exención de matrícula académica y apoyo de instalación."
            }
        ]
    return programs

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_program(
    program_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role(["admin"]))
):
    """
    Creates an academic program (Admin only).
    """
    new_prog = Program(
        title=program_data.get("title"),
        description=program_data.get("description", ""),
        type=program_data.get("type", "scholarship"),
        organization=program_data.get("organization", "EduServer"),
        country=program_data.get("country", "Global"),
        eligibility=program_data.get("eligibility"),
        benefits=program_data.get("benefits"),
        is_active=True
    )
    db.add(new_prog)
    await db.commit()
    await db.refresh(new_prog)
    return new_prog

# ================= ADMIN ROUTER FOR PROGRAMS =================
admin_programs_router = APIRouter(prefix="/admin/programs", tags=["Admin Programs"])

@admin_programs_router.get("")
async def list_admin_programs(
    status: Optional[str] = None,
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    List all programs, optionally filtered by status (Admin only).
    """
    query = select(Program)
    if status:
        query = query.where(Program.status == status)
    query = query.order_by(Program.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@admin_programs_router.patch("/{id}/approve")
async def approve_program(
    id: int,
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve program/convocatoria (Admin only). Sets status to 'approved'.
    """
    result = await db.execute(select(Program).where(Program.id == id))
    program = result.scalars().first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Convocatoria no encontrada."
        )
    program.status = "approved"
    await db.commit()
    await db.refresh(program)
    return program

@admin_programs_router.patch("/{id}/reject")
async def reject_program(
    id: int,
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Reject program/convocatoria (Admin only). Sets status to 'rejected'.
    """
    result = await db.execute(select(Program).where(Program.id == id))
    program = result.scalars().first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Convocatoria no encontrada."
        )
    program.status = "rejected"
    await db.commit()
    await db.refresh(program)
    return program

@admin_programs_router.put("/{id}")
async def update_program_by_admin(
    id: int,
    program_data: dict,
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates program/convocatoria details (Admin only).
    """
    result = await db.execute(select(Program).where(Program.id == id))
    program = result.scalars().first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Convocatoria no encontrada."
        )

    for key, value in program_data.items():
        if key in ["id", "created_at", "updated_at", "slug", "organization_id"]:
            continue
        if hasattr(program, key):
            # Parse dates if key is deadline
            if key == "deadline" and isinstance(value, str) and value:
                import datetime
                try:
                    value = datetime.date.fromisoformat(value)
                except Exception:
                    value = None
            setattr(program, key, value)

    await db.commit()
    await db.refresh(program)
    return program

@admin_programs_router.delete("/{id}")
async def delete_program_by_admin(
    id: int,
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Deletes a program/convocatoria and cleans up related applications (Admin only).
    """
    result = await db.execute(select(Program).where(Program.id == id))
    program = result.scalars().first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Convocatoria no encontrada."
        )

    from app.applications.models import Application, ApplicationStatusHistory
    app_result = await db.execute(select(Application).where(Application.program_id == id))
    apps = app_result.scalars().all()
    app_ids = [a.id for a in apps]

    if app_ids:
        from sqlalchemy import delete
        await db.execute(delete(ApplicationStatusHistory).where(ApplicationStatusHistory.application_id.in_(app_ids)))
        await db.execute(delete(Application).where(Application.id.in_(app_ids)))

    await db.delete(program)
    await db.commit()
    return {"detail": "Convocatoria y sus dependencias eliminadas con éxito."}
