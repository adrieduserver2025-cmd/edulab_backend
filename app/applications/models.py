import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    program_id: Mapped[int] = mapped_column(Integer, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)  # draft, submitted, under_review, accepted, rejected
    applied_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    motivation_letter_draft: Mapped[Optional[str]] = mapped_column(Text)
    ai_review_feedback: Mapped[Optional[str]] = mapped_column(Text)  # Stores IA CV check & compatibility report
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="applications")
    program: Mapped["Program"] = relationship("Program", back_populates="applications")

    def __repr__(self) -> str:
        return f"<Application student={self.student_profile_id} program={self.program_id} status={self.status}>"
