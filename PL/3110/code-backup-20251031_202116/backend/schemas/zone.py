from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class ZoneBase(BaseModel):
    name: str
    topic_name: str
    description: Optional[str] = None

class ZoneCreate(ZoneBase):
    device_id: str
    company_id: Optional[str] = None

class ZoneResponse(ZoneBase):
    id: uuid.UUID
    device_id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
