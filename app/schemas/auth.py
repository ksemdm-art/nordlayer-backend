from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserInDB"

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    is_admin: bool = False

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# Forward reference resolution
from .user import UserInDB
LoginResponse.model_rebuild()