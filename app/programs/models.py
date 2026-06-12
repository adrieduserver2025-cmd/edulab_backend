import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, Date, Text, Integer, func, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class Program(Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # scholarship, volunteering, exchange, leadership, summer_school
    organization: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    deadline: Mapped[Optional[datetime.date]] = mapped_column(Date)
    eligibility: Mapped[Optional[str]] = mapped_column(Text)
    benefits: Mapped[Optional[str]] = mapped_column(Text)
    slots: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Rich Details Fields
    slug: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    organization_name: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[Optional[str]] = mapped_column(String(50), default="open")  # open, closed
    short_description: Mapped[Optional[str]] = mapped_column(Text)
    activities: Mapped[Optional[list]] = mapped_column(JSON)
    requirements: Mapped[Optional[list]] = mapped_column(JSON)
    benefits_json: Mapped[Optional[list]] = mapped_column(JSON)
    dates_info: Mapped[Optional[str]] = mapped_column(String(255))
    support_ai: Mapped[Optional[list]] = mapped_column(JSON)
    facebook_url: Mapped[Optional[str]] = mapped_column(String(500))
    instagram_url: Mapped[Optional[str]] = mapped_column(String(500))
    youtube_url: Mapped[Optional[str]] = mapped_column(String(500))
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Custom Questions and Requirements config
    required_documents: Mapped[Optional[list]] = mapped_column(JSON)
    custom_questions: Mapped[Optional[list]] = mapped_column(JSON)
    required_profile_fields: Mapped[Optional[list]] = mapped_column(JSON)
    
    # Organization link
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="program")
    organization_rel: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="programs")

    def __repr__(self) -> str:
        return f"<Program {self.title} ({self.type}) slug={self.slug}>"
