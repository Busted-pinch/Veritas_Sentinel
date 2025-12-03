# backend/app/db/models/user.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "user"  # "user" or "admin"


class UserInDB(BaseModel):
    user_id: str
    name: Optional[str] = None
    email: EmailStr
    password_hash: str
    role: str
    created_at: datetime
    status: str = "active"
    user_code: Optional[str] = None  # human-readable ID


class UserPublic(BaseModel):
    user_id: str          # internal Mongo id (string)
    user_code: str        # human-readable id
    name: Optional[str]
    email: EmailStr
    role: str
