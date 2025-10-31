from sqlalchemy import Column, Float, Integer, DateTime, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Telemetry(Base):
    __tablename__ = "telemetry"
    
    time = Column(DateTime, primary_key=True, default=datetime.utcnow)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), primary_key=True)
    
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=True)
    
    temperature = Column(Float)
    humidity = Column(Float)
    light_level = Column(Float)
    
    x_relays = Column(Integer, default=0)
    y_relays = Column(Integer, default=0)
    
    raw_data = Column(JSON)
    
    device = relationship("Device", back_populates="telemetry")
    
    __table_args__ = (
        Index('idx_telemetry_time_device', 'time', 'device_id'),
        Index('idx_telemetry_company_time', 'company_id', 'time'),
    )
