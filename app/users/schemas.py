import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, ConfigDict

RoleType = Literal["student", "admin", "mentor", "reviewer", "organization"]
OriginType = Literal["external_user", "eduserver_student"]

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    firebase_uid: str
    full_name: Optional[str] = None
    photo_url: Optional[str] = None
    role: Optional[RoleType] = "student"
    origin: Optional[OriginType] = "external_user"
    is_verified: Optional[bool] = False

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    photo_url: Optional[str] = None
    role: Optional[RoleType] = None
    status: Optional[str] = None
    last_login: Optional[datetime.datetime] = None
    is_verified: Optional[bool] = None

class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    firebase_uid: str
    full_name: Optional[str]
    photo_url: Optional[str]
    role: str
    status: str
    origin: str
    last_login: Optional[datetime.datetime]
    is_verified: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
