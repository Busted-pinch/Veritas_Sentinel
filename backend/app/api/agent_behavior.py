# backend/app/api/agent_behavior.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.app.services.behavior_summary_service import generate_behavior_summary
from backend.app.core.security import get_current_admin

router = APIRouter()


class BehaviorRequest(BaseModel):
    user_id: str


@router.post("/behavior-summary")
def behavior_summary(req: BehaviorRequest, admin: dict = Depends(get_current_admin)):
    """
    Admin-only: summarize last 30 days of user behavior.
    """
    return generate_behavior_summary(req.user_id)
