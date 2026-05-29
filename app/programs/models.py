import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, Date, Text, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

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

    # Relationships
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="program")

    def __repr__(self) -> str:
        return f"<Program {self.title} ({self.type})>"
