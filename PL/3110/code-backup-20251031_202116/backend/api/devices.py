from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.deps import require_manager, get_current_user
from app.models.device import Device
from app.models.user import User
from app.models.user_device import UserDevice
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.schemas.user_device import UserDeviceAssign, UserDeviceResponse

router = APIRouter()

@router.get("/", response_model=List[DeviceResponse])
def get_devices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get devices based on role:
    - Admin/Superuser: All devices in all companies
    - Manager: All devices in their company
    - User: Only devices assigned to them
    """
    if current_user.role == "admin" or current_user.is_superuser:
        # Admins see all devices
        devices = db.query(Device).offset(skip).limit(limit).all()
    elif current_user.role == "manager":
        # Managers see all devices in their company
        devices = db.query(Device).filter(
            Device.company_id == current_user.company_id
        ).offset(skip).limit(limit).all()
    else:
        # Regular users only see assigned devices
        device_ids = db.query(UserDevice.device_id).filter(
            UserDevice.user_id == current_user.id
        ).all()
        device_ids = [d[0] for d in device_ids]
        
        devices = db.query(Device).filter(
            Device.id.in_(device_ids) if device_ids else False
        ).offset(skip).limit(limit).all()
    
    return devices

@router.post("/", response_model=DeviceResponse)
def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Create device - Manager or Admin"""
    # Check if device number already exists in company
    existing = db.query(Device).filter(
        Device.device_number == device.device_number,
        Device.company_id == current_user.company_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Device number already exists in this company"
        )
    
    # Generate topic name
    topic_name = f"company/{current_user.company_id}/device/{device.device_number}"
    
    db_device = Device(
        device_number=device.device_number,
        name=device.name,
        description=device.description,
        company_id=current_user.company_id,
        topic_name=topic_name,
        is_active=True,
        is_online=False
    )
    
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    
    return db_device

@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: UUID,
    device: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Update device - Manager or Admin"""
    db_device = db.query(Device).filter(Device.id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Managers can only update devices in their company
    if current_user.role == "manager" and not current_user.is_superuser:
        if db_device.company_id != current_user.company_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot update device in another company"
            )
    
    update_data = device.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_device, field, value)
    
    db.commit()
    db.refresh(db_device)
    
    return db_device

@router.delete("/{device_id}")
def delete_device(
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Delete device - Manager or Admin"""
    db_device = db.query(Device).filter(Device.id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Managers can only delete devices in their company
    if current_user.role == "manager" and not current_user.is_superuser:
        if db_device.company_id != current_user.company_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot delete device in another company"
            )
    
    db.delete(db_device)
    db.commit()
    
    return {"message": "Device deleted successfully"}

# User-Device Assignment Endpoints
@router.post("/{device_id}/assign", response_model=UserDeviceResponse)
def assign_device_to_user(
    device_id: UUID,
    assignment: UserDeviceAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Assign device to user - Manager or Admin"""
    # Verify device exists and belongs to company
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if current_user.role == "manager" and not current_user.is_superuser:
        if device.company_id != current_user.company_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot assign device from another company"
            )
    
    # Verify user exists and belongs to same company
    user = db.query(User).filter(User.id == assignment.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.company_id != device.company_id:
        raise HTTPException(
            status_code=400,
            detail="User and device must belong to the same company"
        )
    
    # Check if already assigned
    existing = db.query(UserDevice).filter(
        UserDevice.user_id == assignment.user_id,
        UserDevice.device_id == device_id
    ).first()
    
    if existing:
        # Update access level
        existing.access_level = assignment.access_level
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new assignment
    db_assignment = UserDevice(
        user_id=assignment.user_id,
        device_id=device_id,
        access_level=assignment.access_level,
        assigned_by=current_user.id
    )
    
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    
    return db_assignment

@router.delete("/{device_id}/unassign/{user_id}")
def unassign_device_from_user(
    device_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Unassign device from user - Manager or Admin"""
    assignment = db.query(UserDevice).filter(
        UserDevice.device_id == device_id,
        UserDevice.user_id == user_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    db.delete(assignment)
    db.commit()
    
    return {"message": "Device unassigned successfully"}

@router.get("/{device_id}/assignments", response_model=List[UserDeviceResponse])
def get_device_assignments(
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get all user assignments for a device"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if current_user.role == "manager" and not current_user.is_superuser:
        if device.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    assignments = db.query(UserDevice).filter(
        UserDevice.device_id == device_id
    ).all()
    
    return assignments
