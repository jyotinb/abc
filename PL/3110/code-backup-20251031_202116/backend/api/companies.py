from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.deps import require_admin, get_current_user
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse

router = APIRouter()

@router.get("/", response_model=List[CompanyResponse])
def get_companies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get companies - Admin sees all, others see only their company"""
    if current_user.role == "admin" or current_user.is_superuser:
        companies = db.query(Company).offset(skip).limit(limit).all()
    else:
        # Non-admins only see their company
        companies = db.query(Company).filter(
            Company.id == current_user.company_id
        ).all()
    return companies

@router.post("/", response_model=CompanyResponse)
def create_company(
    company: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create company - Admin only"""
    # Check if company with same name exists
    existing = db.query(Company).filter(Company.name == company.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company name already exists")
    
    db_company = Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: UUID,
    company: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update company - Admin only"""
    db_company = db.query(Company).filter(Company.id == company_id).first()
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Update fields if provided
    update_data = company.dict(exclude_unset=True)
    
    # Check for name uniqueness if name is being updated
    if "name" in update_data:
        existing = db.query(Company).filter(
            Company.name == update_data["name"],
            Company.id != company_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Company name already exists")
    
    for field, value in update_data.items():
        setattr(db_company, field, value)
    
    db.commit()
    db.refresh(db_company)
    return db_company

@router.delete("/{company_id}")
def delete_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete company - Admin only"""
    db_company = db.query(Company).filter(Company.id == company_id).first()
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    users_count = db.query(User).filter(User.company_id == company_id).count()
    if users_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete company with {users_count} users"
        )
    
    db.delete(db_company)
    db.commit()
    return {"message": "Company deleted successfully"}

@router.get("/{company_id}/users", response_model=List[dict])
def get_company_users(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users in a company"""
    from app.models.user import User as UserModel
    
    # Check if user can access this company
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = db.query(UserModel).filter(UserModel.company_id == company_id).all()
    
    return [
        {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
        for user in users
    ]

@router.get("/{company_id}/devices", response_model=List[dict])
def get_company_devices(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all devices in a company"""
    from app.models.device import Device
    
    # Check if user can access this company
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    devices = db.query(Device).filter(Device.company_id == company_id).all()
    
    return [
        {
            "id": str(device.id),
            "name": device.name,
            "device_number": device.device_number,
            "is_active": device.is_active,
            "is_online": device.is_online,
            "created_at": device.created_at.isoformat()
        }
        for device in devices
    ]

@router.get("/{company_id}/zones", response_model=List[dict])
def get_company_zones(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all zones in a company"""
    from app.models.zone import Zone
    
    # Check if user can access this company
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    zones = db.query(Zone).filter(Zone.company_id == company_id).all()
    
    return [
        {
            "id": str(zone.id),
            "name": zone.name,
            "topic_name": zone.topic_name,
            "created_at": zone.created_at.isoformat()
        }
        for zone in zones
    ]

@router.get("/{company_id}/users", response_model=List[dict])
def get_company_users(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users in a company"""
    from app.models.user import User as UserModel
    
    # Check if user can access this company
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = db.query(UserModel).filter(UserModel.company_id == company_id).all()
    
    return [
        {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
        for user in users
    ]

@router.get("/{company_id}/devices", response_model=List[dict])
def get_company_devices(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all devices in a company"""
    from app.models.device import Device
    
    # Check if user can access this company
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    devices = db.query(Device).filter(Device.company_id == company_id).all()
    
    return [
        {
            "id": str(device.id),
            "name": device.name,
            "device_number": device.device_number,
            "is_active": device.is_active,
            "is_online": device.is_online,
            "created_at": device.created_at.isoformat()
        }
        for device in devices
    ]

@router.get("/{company_id}/zones", response_model=List[dict])
def get_company_zones(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all zones in a company"""
    from app.models.zone import Zone
    
    # Check if user can access this company
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    zones = db.query(Zone).filter(Zone.company_id == company_id).all()
    
    return [
        {
            "id": str(zone.id),
            "name": zone.name,
            "topic_name": zone.topic_name,
            "created_at": zone.created_at.isoformat()
        }
        for zone in zones
    ]

@router.get("/{company_id}/users", response_model=List[dict])
def get_company_users(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users in a company"""
    from app.models.user import User as UserModel
    
    # Check if user can access this company
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = db.query(UserModel).filter(UserModel.company_id == company_id).all()
    
    return [
        {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
        for user in users
    ]

@router.get("/{company_id}/devices", response_model=List[dict])
def get_company_devices(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all devices in a company"""
    from app.models.device import Device
    
    # Check if user can access this company
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    devices = db.query(Device).filter(Device.company_id == company_id).all()
    
    return [
        {
            "id": str(device.id),
            "name": device.name,
            "device_number": device.device_number,
            "is_active": device.is_active,
            "is_online": device.is_online,
            "created_at": device.created_at.isoformat()
        }
        for device in devices
    ]

@router.get("/{company_id}/zones", response_model=List[dict])
def get_company_zones(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all zones in a company"""
    from app.models.zone import Zone
    
    # Check if user can access this company
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    zones = db.query(Zone).filter(Zone.company_id == company_id).all()
    
    return [
        {
            "id": str(zone.id),
            "name": zone.name,
            "topic_name": zone.topic_name,
            "created_at": zone.created_at.isoformat()
        }
        for zone in zones
    ]

@router.get("/{company_id}/users", response_model=List[dict])
def get_company_users(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users in a company"""
    from app.models.user import User as UserModel
    
    # Check if user can access this company
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = db.query(UserModel).filter(UserModel.company_id == company_id).all()
    
    return [
        {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
        for user in users
    ]

@router.get("/{company_id}/devices", response_model=List[dict])
def get_company_devices(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all devices in a company"""
    from app.models.device import Device
    
    # Check if user can access this company
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    devices = db.query(Device).filter(Device.company_id == company_id).all()
    
    return [
        {
            "id": str(device.id),
            "name": device.name,
            "device_number": device.device_number,
            "is_active": device.is_active,
            "is_online": device.is_online,
            "created_at": device.created_at.isoformat()
        }
        for device in devices
    ]

@router.get("/{company_id}/zones", response_model=List[dict])
def get_company_zones(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all zones in a company"""
    from app.models.zone import Zone
    
    # Check if user can access this company
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    zones = db.query(Zone).filter(Zone.company_id == company_id).all()
    
    return [
        {
            "id": str(zone.id),
            "name": zone.name,
            "topic_name": zone.topic_name,
            "created_at": zone.created_at.isoformat()
        }
        for zone in zones
    ]

@router.get("/{company_id}/users", response_model=List[dict])
def get_company_users(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users in a company"""
    from app.models.user import User as UserModel
    
    # Check if user can access this company
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = db.query(UserModel).filter(UserModel.company_id == company_id).all()
    
    return [
        {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
        for user in users
    ]

@router.get("/{company_id}/devices", response_model=List[dict])
def get_company_devices(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all devices in a company"""
    from app.models.device import Device
    
    # Check if user can access this company
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    devices = db.query(Device).filter(Device.company_id == company_id).all()
    
    return [
        {
            "id": str(device.id),
            "name": device.name,
            "device_number": device.device_number,
            "is_active": device.is_active,
            "is_online": device.is_online,
            "created_at": device.created_at.isoformat()
        }
        for device in devices
    ]

@router.get("/{company_id}/zones", response_model=List[dict])
def get_company_zones(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all zones in a company"""
    from app.models.zone import Zone
    
    # Check if user can access this company
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    zones = db.query(Zone).filter(Zone.company_id == company_id).all()
    
    return [
        {
            "id": str(zone.id),
            "name": zone.name,
            "topic_name": zone.topic_name,
            "created_at": zone.created_at.isoformat()
        }
        for zone in zones
    ]

@router.get("/{company_id}/users", response_model=List[dict])
def get_company_users(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users in a company"""
    from app.models.user import User as UserModel
    
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = db.query(UserModel).filter(UserModel.company_id == company_id).all()
    
    return [
        {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
        for user in users
    ]

@router.get("/{company_id}/devices", response_model=List[dict])
def get_company_devices(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all devices in a company"""
    from app.models.device import Device
    
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    devices = db.query(Device).filter(Device.company_id == company_id).all()
    
    return [
        {
            "id": str(device.id),
            "name": device.name,
            "device_number": device.device_number,
            "is_active": device.is_active,
            "is_online": device.is_online,
            "created_at": device.created_at.isoformat()
        }
        for device in devices
    ]

@router.get("/{company_id}/users")
async def get_company_users(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users in a company"""
    from app.models.user import User as UserModel
    
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = db.query(UserModel).filter(UserModel.company_id == company_id).all()
    
    return [
        {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.name or user.name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        for user in users
    ]

@router.get("/{company_id}/devices")
async def get_company_devices(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all devices in a company"""
    from app.models.device import Device
    
    if current_user.role != "admin" and str(current_user.company_id) != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    devices = db.query(Device).filter(Device.company_id == company_id).all()
    
    return [
        {
            "id": str(device.id),
            "name": device.name,
            "device_number": device.device_number,
            "is_active": device.is_active,
            "is_online": device.is_online,
            "created_at": device.created_at.isoformat() if device.created_at else None
        }
        for device in devices
    ]
