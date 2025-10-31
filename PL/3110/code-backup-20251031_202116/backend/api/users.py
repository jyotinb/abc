from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.deps import require_manager, get_current_user
from app.models.user import User
from app.models.company import Company
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import get_password_hash

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get users - Admin sees all, Manager sees company users"""
    if current_user.role == "admin" or current_user.is_superuser:
        users = db.query(User).offset(skip).limit(limit).all()
    else:
        # Managers only see users in their company
        users = db.query(User).filter(
            User.company_id == current_user.company_id
        ).offset(skip).limit(limit).all()
    
    return users

@router.post("/", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Create user - Manager or Admin"""
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Managers can only create users in their company
    if current_user.role == "manager" and not current_user.is_superuser:
        if user.company_id != current_user.company_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot create user in another company"
            )
    
    # Verify company exists if company_id provided
    if user.company_id:
        company = db.query(Company).filter(Company.id == user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
    
    # Validate role
    valid_roles = ["admin", "manager", "user"]
    role = user.role if user.role and user.role in valid_roles else "user"
    
    # Managers cannot create admins
    if current_user.role == "manager" and role == "admin":
        raise HTTPException(
            status_code=403,
            detail="Managers cannot create admin users"
        )
    
    db_user = User(
        email=user.email,
        name=user.name,
        hashed_password=get_password_hash(user.password),
        company_id=user.company_id,
        role=role,
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Update user - Manager or Admin"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Managers can only update users in their company
    if current_user.role == "manager" and not current_user.is_superuser:
        if db_user.company_id != current_user.company_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot update user in another company"
            )
    
    # Update fields
    update_data = user.dict(exclude_unset=True)
    
    # Check email uniqueness if being updated
    if "email" in update_data:
        existing = db.query(User).filter(
            User.email == update_data["email"],
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
    
    # Verify company if being updated
    if "company_id" in update_data and update_data["company_id"]:
        company = db.query(Company).filter(Company.id == update_data["company_id"]).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
    
    # Hash password if being updated
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # Managers cannot change role to admin
    if "role" in update_data and update_data["role"] == "admin":
        if current_user.role == "manager" and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Managers cannot set admin role"
            )
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.delete("/{user_id}")
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Delete user - Manager or Admin"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Cannot delete yourself
    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Managers can only delete users in their company
    if current_user.role == "manager" and not current_user.is_superuser:
        if db_user.company_id != current_user.company_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot delete user in another company"
            )
    
    db.delete(db_user)
    db.commit()
    
    return {"message": "User deleted successfully"}

@router.get("/{user_id}/devices", response_model=List[dict])
def get_user_devices(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get devices accessible by a user"""
    from app.models.device import Device
    
    # Check permissions
    if current_user.role != "admin" and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get devices from user's company
    devices = db.query(Device).filter(Device.company_id == user.company_id).all()
    
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

@router.get("/{user_id}/devices", response_model=List[dict])
def get_user_devices(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get devices accessible by a user"""
    from app.models.device import Device
    
    # Check permissions
    if current_user.role != "admin" and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get devices from user's company
    devices = db.query(Device).filter(Device.company_id == user.company_id).all()
    
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

@router.get("/{user_id}/devices", response_model=List[dict])
def get_user_devices(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get devices accessible by a user"""
    from app.models.device import Device
    
    # Check permissions
    if current_user.role != "admin" and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get devices from user's company
    devices = db.query(Device).filter(Device.company_id == user.company_id).all()
    
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

@router.get("/{user_id}/devices", response_model=List[dict])
def get_user_devices(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get devices accessible by a user"""
    from app.models.device import Device
    
    # Check permissions
    if current_user.role != "admin" and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get devices from user's company
    devices = db.query(Device).filter(Device.company_id == user.company_id).all()
    
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

@router.get("/{user_id}/devices", response_model=List[dict])
def get_user_devices(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get devices accessible by a user"""
    from app.models.device import Device
    
    # Check permissions
    if current_user.role != "admin" and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get devices from user's company
    devices = db.query(Device).filter(Device.company_id == user.company_id).all()
    
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

@router.get("/{user_id}/devices", response_model=List[dict])
def get_user_devices(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get devices accessible by a user"""
    from app.models.device import Device
    
    if current_user.role != "admin" and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    devices = db.query(Device).filter(Device.company_id == user.company_id).all()
    
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

@router.get("/{user_id}/devices")
async def get_user_devices(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get devices accessible by a user"""
    from app.models.device import Device
    
    if current_user.role != "admin" and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    devices = db.query(Device).filter(Device.company_id == user.company_id).all()
    
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
