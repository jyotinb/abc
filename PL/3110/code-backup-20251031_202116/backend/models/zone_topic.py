from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

class ZoneTopic(Base):
    __tablename__ = "zone_topics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)
    topic_path = Column(String(500), nullable=False)
    direction = Column(String(20))  # 'publish', 'subscribe', or 'both'
    description = Column(Text)
    qos = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("direction IN ('publish', 'subscribe', 'both')", name='zone_topics_direction_check'),
        CheckConstraint("qos IN (0, 1, 2)", name='zone_topics_qos_check'),
    )
    
    # Relationships
    zone = relationship("Zone", back_populates="topics")

class ZoneVariable(Base):
    __tablename__ = "zone_variables"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)
    zone_topic_id = Column(UUID(as_uuid=True), ForeignKey("zone_topics.id", ondelete="CASCADE"))
    variable_name = Column(String(100), nullable=False)
    variable_type = Column(String(50), default="string")
    unit = Column(String(50))
    description = Column(Text)
    min_value = Column(String(50))
    max_value = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    zone = relationship("Zone", back_populates="variables")
    zone_topic = relationship("ZoneTopic", backref="variables")
