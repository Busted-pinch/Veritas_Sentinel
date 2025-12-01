# backend/app/core/security.py

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId

from backend.app.db.mongo import users_col

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# tokenUrl must match your /auth/login path
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------- PASSWORD UTILS ----------

def get_password_hash(password: str) -> str:
    # Bcrypt cannot handle >72 bytes; enforce a limit
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password too long: must be <=72 bytes.")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ---------- JWT CREATION ----------

def create_access_token(
    user_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT with:
    - sub = user_id
    - role = user's role
    """
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "sub": user_id,
        "role": role,
        "exp": expire,
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ---------- USER LOOKUP ----------

def get_user_by_email(email: str):
    return users_col.find_one({"email": email})


def get_user_by_id(user_id: str):
    # look up by Mongo _id, not "user_id"
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    return users_col.find_one({"_id": oid})


# ---------- AUTH DEPENDENCIES ----------

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_id(user_id)
    if user is None:
        raise credentials_exception

    # normalize what downstream sees
    return {
        "user_id": str(user["_id"]),
        "email": user["email"],
        "role": user["role"],
    }


def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
