from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    company = relationship("Company", back_populates="devices")
    
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=True)
    zone = relationship("Zone", back_populates="devices", foreign_keys=[zone_id])
    
    device_number = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    
    topic_name = Column(String, nullable=False)
    mqtt_username = Column(String)
    mqtt_password = Column(String)
    
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime)
    
    config = Column(JSON, default=dict)
    
    telemetry = relationship("Telemetry", back_populates="device")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('company_id', 'device_number', name='uix_company_device'),
    )
