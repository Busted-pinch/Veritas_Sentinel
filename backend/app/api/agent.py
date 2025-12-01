# backend/app/api/agent.py

from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.services.agent_service import speculate_user

router = APIRouter()

class SpeculateRequest(BaseModel):
    user_id: str

@router.post("/speculate")
def speculate(req: SpeculateRequest):
    """
    LLM-powered speculation agent.
    Input: user_id
    Output: speculation score, narrative explanation, indicators
    """
    return speculate_user(req.user_id)
