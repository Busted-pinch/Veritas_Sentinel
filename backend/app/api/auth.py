# backend/app/api/auth.py

from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_admin,
)
from backend.app.db.mongo import users_col
from backend.app.db.models.user import UserCreate, UserPublic

router = APIRouter()


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

    user_doc = {
        "email": payload.email,
        "password_hash": password_hash,
        "role": payload.role,
        "created_at": datetime.utcnow(),
        "status": "active",
    }

    result = users_col.insert_one(user_doc)
    user_id = str(result.inserted_id)

    return UserPublic(
        user_id=user_id,
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
            "user_id": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
        }
    }
