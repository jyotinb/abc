from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.deps import require_manager, get_current_user
from app.models.zone import Zone
from app.models.device import Device
from app.models.user import User
from app.schemas.zone import ZoneCreate, ZoneResponse

router = APIRouter()

@router.get("/", response_model=List[ZoneResponse])
def get_zones(
    device_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get zones - Users only see zones from their company's devices"""
    query = db.query(Zone).filter(Zone.company_id == current_user.company_id)
    
    if device_id:
        # Verify device belongs to user's company
        device = db.query(Device).filter(
            Device.id == device_id,
            Device.company_id == current_user.company_id
        ).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        query = query.filter(Zone.device_id == device_id)
    
    zones = query.all()
    return zones

@router.post("/", response_model=ZoneResponse)
def create_zone(
    zone: ZoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Create zone - Manager or Admin, must be for device in their company"""
    # Verify device belongs to user's company
    device = db.query(Device).filter(
        Device.id == zone.device_id,
        Device.company_id == current_user.company_id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=404, 
            detail="Device not found or access denied"
        )
    
    # Auto-assign to current user's company
    db_zone = Zone(
        name=zone.name,
        topic_name=zone.topic_name,
        description=zone.description,
        device_id=zone.device_id,
        company_id=current_user.company_id
    )
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone
