from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class DeviceBase(BaseModel):
    device_number: str
    name: str
    description: Optional[str] = None

class DeviceCreate(DeviceBase):
    company_id: Optional[str] = None

class DeviceUpdate(DeviceBase):
    device_number: Optional[str] = None
    name: Optional[str] = None

class DeviceResponse(DeviceBase):
    id: uuid.UUID
    company_id: uuid.UUID
    topic_name: str
    is_active: bool
    is_online: bool
    last_seen: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
