# backend/app/db/models/user.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"  # "user" or "admin"


class UserInDB(BaseModel):
    user_id: str
    email: EmailStr
    password_hash: str
    role: str
    created_at: datetime
    status: str = "active"


class UserPublic(BaseModel):
    user_id: str
    email: EmailStr
    role: str
