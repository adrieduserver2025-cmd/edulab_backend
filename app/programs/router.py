from typing import List
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
    List all active educational programs (scholarships, leadership, summer schools, etc.).
    """
    result = await db.execute(select(Program).where(Program.is_active == True))
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
