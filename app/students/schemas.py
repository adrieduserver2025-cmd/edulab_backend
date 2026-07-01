import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date

def parse_date_string(v):
    if not v:
        return None
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        v = v.strip()
        if not v:
            return None
        # Try YYYY-MM-DD
        try:
            return datetime.datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            pass
        # Try DD/MM/YYYY
        try:
            return datetime.datetime.strptime(v, "%d/%m/%Y").date()
        except ValueError:
            pass
        # Try MM/DD/YYYY
        try:
            return datetime.datetime.strptime(v, "%m/%d/%Y").date()
        except ValueError:
            pass
    return v

class StudentProfileBase(BaseModel):
    country: str = Field(..., description="Country of residence")
    city: str = Field(..., description="City of residence")
    birth_date: date = Field(..., description="Birth date (YYYY-MM-DD)")
    phone: str = Field(..., description="Contact phone number")
    education_level: str = Field(..., description="Highest education level reached")
    current_institution: Optional[str] = Field(None, description="Current educational institution")
    area: str = Field(..., description="Main study/work area (e.g. STEM, Business, Arts)")
    english_level: str = Field(..., description="English proficiency level")
    other_languages: Optional[List[str]] = Field(default=None, description="Other languages spoken")
    interests: List[str] = Field(..., description="List of primary academic/professional interests")
    target_countries: List[str] = Field(..., description="List of destination countries of interest")
    target_program_types: List[str] = Field(..., description="List of target program types (e.g. scholarship, exchange)")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    portfolio_url: Optional[str] = Field(None, description="Portfolio or personal website URL")
    bio: Optional[str] = Field(None, description="Short bio")
    cv_url: Optional[str] = Field(None, description="Link to uploaded curriculum vitae document")
    expected_graduation_date: Optional[date] = Field(None, description="Expected graduation date (YYYY-MM-DD)")
    work_experience: Optional[List[dict]] = Field(default=None, description="List of work experience items")
    volunteer_experience: Optional[List[dict]] = Field(default=None, description="List of volunteer experience items")
    general_motivation_letter: Optional[str] = Field(None, description="General motivation letter text")

    @field_validator('birth_date', 'expected_graduation_date', mode='before')
    @classmethod
    def validate_dates(cls, v):
        return parse_date_string(v)

class StudentProfileCreate(StudentProfileBase):
    pass

class StudentProfileUpdate(BaseModel):
    country: Optional[str] = None
    city: Optional[str] = None
    birth_date: Optional[date] = None
    phone: Optional[str] = None
    education_level: Optional[str] = None
    current_institution: Optional[str] = None
    area: Optional[str] = None
    english_level: Optional[str] = None
    other_languages: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    target_countries: Optional[List[str]] = None
    target_program_types: Optional[List[str]] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    bio: Optional[str] = None
    cv_url: Optional[str] = None
    expected_graduation_date: Optional[date] = None
    work_experience: Optional[List[dict]] = None
    volunteer_experience: Optional[List[dict]] = None
    general_motivation_letter: Optional[str] = None

    @field_validator('birth_date', 'expected_graduation_date', mode='before')
    @classmethod
    def validate_dates(cls, v):
        return parse_date_string(v)

class StudentProfile(StudentProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    profile_completion: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

