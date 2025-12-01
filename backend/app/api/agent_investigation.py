# backend/app/api/agent_investigation.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.app.services.investigation_service import generate_case_file
from backend.app.core.security import get_current_admin

router = APIRouter()


class InvestigationRequest(BaseModel):
    user_id: str


@router.post("/investigation")
def investigation(req: InvestigationRequest, admin: dict = Depends(get_current_admin)):
    """
    Admin-only: generate a detailed fraud investigation case file.
    """
    return generate_case_file(req.user_id)
