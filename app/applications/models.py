import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    program_id: Mapped[int] = mapped_column(Integer, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="started", nullable=False)  # started, pending, in_review, accepted, rejected
    applied_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    motivation_letter_draft: Mapped[Optional[str]] = mapped_column(Text)
    ai_review_feedback: Mapped[Optional[str]] = mapped_column(Text)  # Stores IA CV check & compatibility report
    
    # Custom postulation inputs
    answers: Mapped[Optional[list]] = mapped_column(JSON)
    uploaded_documents: Mapped[Optional[dict]] = mapped_column(JSON)
    
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    student_profile: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="applications")
    program: Mapped["Program"] = relationship("Program", back_populates="applications")
    status_history: Mapped[list["ApplicationStatusHistory"]] = relationship("ApplicationStatusHistory", back_populates="application", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Application student={self.student_profile_id} program={self.program_id} status={self.status}>"


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    application = relationship("Application", back_populates="status_history")
    changed_by_user = relationship("User")

    def __repr__(self) -> str:
        return f"<ApplicationStatusHistory application_id={self.application_id} change={self.old_status}->{self.new_status}>"

