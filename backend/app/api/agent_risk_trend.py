# backend/app/api/agent_risk_trend.py

from fastapi import APIRouter, Depends

from backend.app.services.risk_trend_service import get_risk_trend
from backend.app.core.security import get_current_admin

router = APIRouter()


@router.get("/risk-trend/{user_id}")
def risk_trend(user_id: str, admin: dict = Depends(get_current_admin)):
    """
    Admin-only: get 30-day risk/anomaly/trust trend for a user.
    """
    return get_risk_trend(user_id)
