from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255))
    photo_url = Column(String)
    role = Column(String(50), default="student")
    status = Column(String(50), default="active")
    origin = Column(String(50), default="external_user", nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationship to student profile (1-to-1)
    student_profile = relationship(
        "StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    # Relationship to organization profile (1-to-1)
    organization = relationship(
        "Organization", back_populates="user", uselist=False, cascade="all, delete-orphan", foreign_keys="[Organization.user_id]"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
