import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database.base import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Organization Details
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)  # ONG, Universidad, Fundación, Empresa, Organismo Internacional, Otro
    country = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    website = Column(String(255), nullable=True)
    social_links = Column(JSON, nullable=True)  # Store social media links as JSON (e.g. {"facebook": "...", "linkedin": "..."})
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    
    # Responsible/Contact Details
    contact_name = Column(String(255), nullable=False)
    contact_position = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    
    # Verification and Status
    verification_document_url = Column(String(500), nullable=True)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED
    
    # Metadata and Logs
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="organization", foreign_keys=[user_id])
    approver = relationship("User", foreign_keys=[approved_by])
    programs = relationship("Program", back_populates="organization_rel", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Organization {self.name} status={self.status}>"
