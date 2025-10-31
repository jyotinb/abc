from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class ZoneTopicBase(BaseModel):
    topic_path: str = Field(..., max_length=500, description="MQTT topic path")
    direction: str = Field(..., pattern="^(publish|subscribe|both)$")
    description: Optional[str] = None
    qos: int = Field(default=1, ge=0, le=2)
    is_active: bool = True

class ZoneTopicCreate(ZoneTopicBase):
    pass

class ZoneTopicUpdate(BaseModel):
    topic_path: Optional[str] = Field(None, max_length=500)
    direction: Optional[str] = Field(None, pattern="^(publish|subscribe|both)$")
    description: Optional[str] = None
    qos: Optional[int] = Field(None, ge=0, le=2)
    is_active: Optional[bool] = None

class ZoneTopicResponse(ZoneTopicBase):
    id: uuid.UUID
    zone_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
