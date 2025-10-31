from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.deps import get_current_user
from datetime import timedelta
from app.config import settings

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "company_id": str(user.company_id) if user.company_id else None,
            "role": user.role,  # ← ADDED
            "is_superuser": user.is_superuser  # ← ADDED
        }
    )

@router.post("/register")
async def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=data.email,
        name=data.name,
        hashed_password=get_password_hash(data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"message": "User registered successfully", "user_id": str(user.id)}

@router.get("/validate-token")
async def validate_token(current_user: User = Depends(get_current_user)):
    return {
        "valid": True,
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.name,
            "company_id": str(current_user.company_id) if current_user.company_id else None,
            "role": current_user.role,  # ← ADDED
            "is_superuser": current_user.is_superuser  # ← ADDED
        }
    }
