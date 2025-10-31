from sqlalchemy import Column, String, Boolean, DateTime, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False, index=True)
    email = Column(String)
    phone = Column(String)
    address = Column(String)
    
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String, default="basic")
    max_devices = Column(Integer, default=10)
    
    settings = Column(JSON, default=dict)
    
    users = relationship("User", back_populates="company")
    devices = relationship("Device", back_populates="company")
    zones = relationship("Zone", back_populates="company")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
