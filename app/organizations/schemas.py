import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator

class OrganizationBase(BaseModel):
    name: str
    type: str  # ONG, Universidad, Fundación, Empresa, Organismo Internacional, Otro
    country: str
    city: str
    website: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None

class OrganizationRegister(OrganizationBase):
    contact_name: str
    contact_position: str
    contact_email: EmailStr
    contact_phone: str
    password: str
    confirm_password: str
    verification_document_url: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
        return v

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    contact_name: Optional[str] = None
    contact_position: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    verification_document_url: Optional[str] = None
    status: Optional[str] = None

class OrganizationResponse(OrganizationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    contact_name: str
    contact_position: str
    contact_email: str
    contact_phone: str
    verification_document_url: Optional[str]
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    approved_at: Optional[datetime.datetime]
    approved_by: Optional[int]

class OrganizationApplicantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_profile_id: int
    program_id: int
    status: str
    applied_at: Optional[datetime.datetime]
    created_at: datetime.datetime
    
    # Custom postulation values
    answers: Optional[List[Dict[str, Any]]] = None
    uploaded_documents: Optional[Dict[str, Any]] = None
    status_history: Optional[List[Dict[str, Any]]] = None
    
    # Program Info
    program_title: str
    program_slug: str
    
    # Student Info
    student_name: str
    student_email: str
    student_phone: str
    student_country: str
    student_city: str
    student_education_level: str
    student_current_institution: Optional[str] = None
    student_cv_url: Optional[str] = None
    student_bio: Optional[str] = None
    student_birth_date: Optional[datetime.date] = None
    student_area: Optional[str] = None
    student_english_level: Optional[str] = None
    student_other_languages: Optional[List[str]] = None
    student_expected_graduation_date: Optional[datetime.date] = None
    student_work_experience: Optional[List[Dict[str, Any]]] = None
    student_volunteer_experience: Optional[List[Dict[str, Any]]] = None
    student_general_motivation_letter: Optional[str] = None
    student_linkedin_url: Optional[str] = None
    student_portfolio_url: Optional[str] = None
