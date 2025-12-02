from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from backend.app.core.security import get_current_admin
from backend.app.db.mongo import users_col
from bson import ObjectId

router = APIRouter()


@router.get("/users")
def list_users(
    q: Optional[str] = Query(None, description="Email search substring"),
    limit: int = 50,
    admin: dict = Depends(get_current_admin),
) -> List[dict]:
    """
    Admin-only: list users with basic info.
    Supports simple email substring search.
    """

    query = {}
    if q:
        query = {"email": {"$regex": q, "$options": "i"}}

    cursor = users_col.find(query).sort("created_at", -1).limit(limit)

    users = []
    for u in cursor:
        users.append(
            {
                "user_id": str(u["_id"]),
                "email": u.get("email"),
                "role": u.get("role"),
                "status": u.get("status", "active"),
                "created_at": u.get("created_at"),
            }
        )
    return users
