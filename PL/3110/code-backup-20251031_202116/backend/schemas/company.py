from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class CompanyBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = True
    subscription_tier: Optional[str] = "basic"
    max_devices: Optional[int] = 10

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None
    subscription_tier: Optional[str] = None
    max_devices: Optional[int] = None

class CompanyResponse(BaseModel):
    id: UUID  # Changed from str to UUID
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None
    subscription_tier: Optional[str] = None
    max_devices: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
