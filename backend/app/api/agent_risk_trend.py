from fastapi import APIRouter
from backend.app.services.risk_trend_service import get_risk_trend

router = APIRouter()

@router.get("/risk-trend/{user_id}")
def risk_trend(user_id: str):
    return get_risk_trend(user_id)
