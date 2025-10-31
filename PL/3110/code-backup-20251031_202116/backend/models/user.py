from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Company relationship (required for non-superusers)
    company_id = Column(String, ForeignKey("companies.id"), nullable=True)
    company = relationship("Company", back_populates="users")
    
    # Role: 'admin', 'manager', 'user'
    role = Column(String, default="user", nullable=False)
    
    # Optional: Store additional permissions as JSON
    permissions = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
