from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.students.models import StudentProfile
from app.students.schemas import StudentProfileCreate, StudentProfileUpdate

def calculate_profile_completion(data: Any) -> int:
    """
    Dynamically calculates the profile completion percentage based on 10 fields:
    country, city, birth_date, phone, education_level, area, english_level,
    interests, target_countries, target_program_types.
    
    Each complete field adds 10%.
    """
    required_fields = [
        "country",
        "city",
        "birth_date",
        "phone",
        "education_level",
        "area",
        "english_level",
        "interests",
        "target_countries",
        "target_program_types"
    ]
    completed = 0
    
    for field in required_fields:
        if isinstance(data, dict):
            val = data.get(field)
        else:
            val = getattr(data, field, None)
            
        if val is not None:
            # String empty/whitespace validation
            if isinstance(val, str) and val.strip() == "":
                continue
            # List/array empty validation
            if isinstance(val, (list, dict)) and len(val) == 0:
                continue
            completed += 1
            
    return int((completed / len(required_fields)) * 100)

async def get_profile_by_user_id(db: AsyncSession, user_id: int) -> Optional[StudentProfile]:
    """
    Fetch a student profile by their associated user_id.
    """
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    return result.scalars().first()

async def create_profile(db: AsyncSession, profile_in: StudentProfileCreate, user_id: int) -> StudentProfile:
    """
    Create a new student profile and link it to the user.
    """
    completion = calculate_profile_completion(profile_in.model_dump())
    
    db_profile = StudentProfile(
        user_id=user_id,
        country=profile_in.country,
        city=profile_in.city,
        birth_date=profile_in.birth_date,
        phone=profile_in.phone,
        education_level=profile_in.education_level,
        current_institution=profile_in.current_institution,
        area=profile_in.area,
        english_level=profile_in.english_level,
        other_languages=profile_in.other_languages,
        interests=profile_in.interests,
        target_countries=profile_in.target_countries,
        target_program_types=profile_in.target_program_types,
        linkedin_url=profile_in.linkedin_url,
        portfolio_url=profile_in.portfolio_url,
        bio=profile_in.bio,
        cv_url=profile_in.cv_url,
        profile_completion=completion
    )
    
    db.add(db_profile)
    await db.commit()
    await db.refresh(db_profile)
    return db_profile

async def update_profile(db: AsyncSession, profile_in: StudentProfileUpdate, user_id: int) -> Optional[StudentProfile]:
    """
    Update an existing student profile. Re-calculates and persists completion metric.
    """
    db_profile = await get_profile_by_user_id(db, user_id)
    if not db_profile:
        return None
        
    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_profile, field, value)
        
    # Re-calculate completion
    db_profile.profile_completion = calculate_profile_completion(db_profile)
    
    await db.commit()
    await db.refresh(db_profile)
    return db_profile
