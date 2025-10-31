from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm_password: str

class TokenRefresh(BaseModel):
    refresh_token: str
