import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Date, JSON, Text, func
from sqlalchemy.orm import relationship
from app.database.base import Base

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    country = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    birth_date = Column(Date, nullable=False)
    phone = Column(String(50), nullable=False)
    education_level = Column(String(100), nullable=False)
    current_institution = Column(String(255), nullable=True)
    area = Column(String(100), nullable=False)
    english_level = Column(String(50), nullable=False)
    other_languages = Column(JSON, nullable=True)
    interests = Column(JSON, nullable=False)
    target_countries = Column(JSON, nullable=False)
    target_program_types = Column(JSON, nullable=False)
    linkedin_url = Column(String(255), nullable=True)
    portfolio_url = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    cv_url = Column(String(500), nullable=True)
    profile_completion = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="student_profile")

    def __repr__(self) -> str:
        return f"<StudentProfile id={self.id} user_id={self.user_id} country={self.country}>"
