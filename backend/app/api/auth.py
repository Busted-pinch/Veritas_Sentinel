# backend/app/api/auth.py

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_admin,
    get_current_user,
)
from backend.app.db.mongo import users_col
from backend.app.db.models.user import UserCreate, UserPublic

router = APIRouter()

def _generate_user_code(name: str) -> str:
    """
    Generate a human-readable user code like 'PRAT-0001'.
    Very simple and not collision-proof, but fine for this project.
    """
    prefix = "".join(c for c in name.upper() if c.isalnum())[:4] or "USER"
    count = users_col.count_documents({}) + 1
    return f"{prefix}-{count:04d}"

@router.get("/me")
def read_me(current_user: dict = Depends(get_current_user)):
    """
    Return current user's basic info from token + DB.
    Good for frontend bootstrapping.
    """
    return {
        "user_id": current_user["user_id"],
        "user_code": current_user.get("user_code"),
        "name": current_user.get("name"),
        "email": current_user["email"],
        "role": current_user["role"],
    }


# ---------- ADMIN-ONLY REGISTER ----------

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, admin: dict = Depends(get_current_admin)):
    """
    Admin-only: create a new user account.
    The caller must have role="admin".
    """
    # check if email already exists
    if users_col.find_one({"email": payload.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    password_hash = get_password_hash(payload.password)
    user_code = _generate_user_code(payload.name)

    user_doc = {
        "name": payload.name,
        "email": payload.email,
        "password_hash": password_hash,
        "role": payload.role,
        "user_code": user_code,
        "created_at": datetime.utcnow(),
        "status": "active",
    }

    result = users_col.insert_one(user_doc)
    user_id = str(result.inserted_id)

    return UserPublic(
        user_id=user_id,
        user_code=user_code,
        name=payload.name,
        email=payload.email,
        role=payload.role,
    )



# ---------- PUBLIC LOGIN (OAuth2 password flow) ----------

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 password-flow login for Swagger UI and other clients.
    - Swagger will send `username` and `password` as form fields.
    - We treat `username` as the email.
    """
    email = form_data.username
    password = form_data.password

    user = users_col.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        user_id=str(user["_id"]),
        role=user["role"],
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": str(user["_id"]),              # internal id
            "user_code": user.get("user_code"),       # human-readable id
            "name": user.get("name"),
            "email": user["email"],
            "role": user["role"],
        }
    }
