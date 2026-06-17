from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.programs.models import Program

router = APIRouter(tags=["Opportunities"])

@router.get("/opportunities")
async def list_opportunities(db: AsyncSession = Depends(get_db)):
    """
    List all active approved opportunities (scholarships, volunteering, exchanges, etc.).
    """
    result = await db.execute(
        select(Program).where(Program.is_active == True, Program.status == "approved").order_by(Program.id)
    )
    return result.scalars().all()

@router.get("/opportunities/{slug}")
async def get_opportunity_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve opportunity details by unique slug.
    """
    result = await db.execute(
        select(Program).where(Program.slug == slug, Program.is_active == True, Program.status == "approved")
    )
    opp = result.scalars().first()
    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity with slug '{slug}' not found."
        )
    return opp

@router.get("/volunteering")
async def list_volunteering(db: AsyncSession = Depends(get_db)):
    """
    List all active approved volunteering opportunities specifically.
    """
    result = await db.execute(
        select(Program).where(Program.type == "volunteering", Program.is_active == True, Program.status == "approved").order_by(Program.id)
    )
    return result.scalars().all()

@router.get("/volunteering/{slug}")
async def get_volunteering_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve volunteering details by unique slug.
    """
    result = await db.execute(
        select(Program).where(Program.slug == slug, Program.type == "volunteering", Program.is_active == True, Program.status == "approved")
    )
    vol = result.scalars().first()
    if not vol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Volunteering opportunity with slug '{slug}' not found."
        )
    return vol
