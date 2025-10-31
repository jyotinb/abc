from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str
    company_id: Optional[UUID] = None
    role: Optional[str] = "user"

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    company_id: Optional[UUID] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserResponse(BaseModel):
    id: UUID  # Changed from str to UUID
    email: EmailStr
    name: str
    company_id: Optional[UUID] = None  # Changed from str to Optional[UUID]
    role: Optional[str] = None
    is_active: bool
    is_superuser: Optional[bool] = None  # Added
    created_at: datetime
    updated_at: Optional[datetime] = None  # Added
    
    class Config:
        from_attributes = True
