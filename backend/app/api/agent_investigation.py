from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.services.investigation_service import generate_case_file

router = APIRouter()

class InvestigationRequest(BaseModel):
    user_id: str

@router.post("/investigation")
def investigation(req: InvestigationRequest):
    return generate_case_file(req.user_id)
