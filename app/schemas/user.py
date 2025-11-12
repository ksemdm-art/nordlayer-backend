from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from .base import BaseSchema, TimestampedSchema

class UserBase(BaseSchema):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    role: str = "user"

class UserCreate(UserBase):
    password: str
    is_admin: bool = False

class UserUpdate(BaseSchema):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    role: Optional[str] = None
    password: Optional[str] = None

class UserInDB(TimestampedSchema, UserBase):
    is_admin: bool = False
    last_login: Optional[datetime] = None

class UserSummary(BaseSchema):
    id: int
    username: str
    full_name: Optional[str] = None

class User(UserInDB):
    pass

class UserWithOrders(User):
    orders: List["OrderSummary"] = []

# Forward reference resolution
from .order import OrderSummary
UserWithOrders.model_rebuild()