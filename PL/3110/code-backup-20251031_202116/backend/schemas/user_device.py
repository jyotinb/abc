from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class UserDeviceAssign(BaseModel):
    user_id: UUID
    device_id: UUID
    access_level: Optional[str] = "read"  # read, write, control

class UserDeviceResponse(BaseModel):
    id: UUID
    user_id: UUID
    device_id: UUID
    access_level: str
    assigned_at: datetime
    assigned_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True
