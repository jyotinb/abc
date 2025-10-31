from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models import User, Zone, ZoneTopic
from app.schemas.zone_topic import ZoneTopicCreate, ZoneTopicUpdate, ZoneTopicResponse
from app.api.auth import get_current_user

router = APIRouter()

def check_zone_access(zone_id: str, current_user: User, db: Session) -> Zone:
    """Check if user has access to zone"""
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    if current_user.role != "admin" and zone.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return zone

@router.get("/zones/{zone_id}/topics", response_model=List[ZoneTopicResponse])
def get_zone_topics(
    zone_id: str,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all topics for a zone"""
    zone = check_zone_access(zone_id, current_user, db)
    
    query = db.query(ZoneTopic).filter(ZoneTopic.zone_id == zone_id)
    if active_only:
        query = query.filter(ZoneTopic.is_active == True)
    
    topics = query.order_by(ZoneTopic.topic_path).all()
    return topics

@router.get("/zones/{zone_id}/topics/{topic_id}", response_model=ZoneTopicResponse)
def get_zone_topic(
    zone_id: str,
    topic_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific zone topic"""
    check_zone_access(zone_id, current_user, db)
    
    topic = db.query(ZoneTopic).filter(
        ZoneTopic.id == topic_id,
        ZoneTopic.zone_id == zone_id
    ).first()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    return topic

@router.post("/zones/{zone_id}/topics", response_model=ZoneTopicResponse, status_code=status.HTTP_201_CREATED)
def create_zone_topic(
    zone_id: str,
    topic_data: ZoneTopicCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new topic for a zone (admin/manager only)"""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admins and managers can create topics")
    
    zone = check_zone_access(zone_id, current_user, db)
    
    # Check if topic already exists
    existing = db.query(ZoneTopic).filter(
        ZoneTopic.zone_id == zone_id,
        ZoneTopic.topic_path == topic_data.topic_path
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Topic '{topic_data.topic_path}' already exists for this zone"
        )
    
    # Create new topic
    new_topic = ZoneTopic(
        zone_id=zone_id,
        **topic_data.dict()
    )
    
    db.add(new_topic)
    db.commit()
    db.refresh(new_topic)
    
    return new_topic

@router.put("/zones/{zone_id}/topics/{topic_id}", response_model=ZoneTopicResponse)
def update_zone_topic(
    zone_id: str,
    topic_id: str,
    topic_data: ZoneTopicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a zone topic (admin/manager only)"""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admins and managers can update topics")
    
    check_zone_access(zone_id, current_user, db)
    
    topic = db.query(ZoneTopic).filter(
        ZoneTopic.id == topic_id,
        ZoneTopic.zone_id == zone_id
    ).first()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Update fields
    update_data = topic_data.dict(exclude_unset=True)
    
    # Check for duplicate topic_path if being updated
    if "topic_path" in update_data and update_data["topic_path"] != topic.topic_path:
        existing = db.query(ZoneTopic).filter(
            ZoneTopic.zone_id == zone_id,
            ZoneTopic.topic_path == update_data["topic_path"],
            ZoneTopic.id != topic_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Topic '{update_data['topic_path']}' already exists"
            )
    
    for field, value in update_data.items():
        setattr(topic, field, value)
    
    topic.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(topic)
    
    return topic

@router.delete("/zones/{zone_id}/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone_topic(
    zone_id: str,
    topic_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a zone topic (admin/manager only)"""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admins and managers can delete topics")
    
    check_zone_access(zone_id, current_user, db)
    
    topic = db.query(ZoneTopic).filter(
        ZoneTopic.id == topic_id,
        ZoneTopic.zone_id == zone_id
    ).first()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    db.delete(topic)
    db.commit()
    
    return None

@router.post("/zones/{zone_id}/topics/{topic_id}/toggle", response_model=ZoneTopicResponse)
def toggle_zone_topic(
    zone_id: str,
    topic_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle active status of a zone topic (admin/manager only)"""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admins and managers can toggle topics")
    
    check_zone_access(zone_id, current_user, db)
    
    topic = db.query(ZoneTopic).filter(
        ZoneTopic.id == topic_id,
        ZoneTopic.zone_id == zone_id
    ).first()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    topic.is_active = not topic.is_active
    topic.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(topic)
    
    return topic
