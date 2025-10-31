from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

class Zone(Base):
    __tablename__ = "zones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    topic_name = Column(String, nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    description = Column(Text)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    mqtt_topic = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="zones")
    devices = relationship("Device", back_populates="zone", foreign_keys="Device.zone_id")
    topics = relationship("ZoneTopic", back_populates="zone", cascade="all, delete-orphan")
    variables = relationship("ZoneVariable", back_populates="zone", cascade="all, delete-orphan")
