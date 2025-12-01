from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.services.behavior_summary_service import generate_behavior_summary

router = APIRouter()

class BehaviorRequest(BaseModel):
    user_id: str

@router.post("/behavior-summary")
def behavior_summary(req: BehaviorRequest):
    return generate_behavior_summary(req.user_id)
