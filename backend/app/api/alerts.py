from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.core.security import get_current_admin
from backend.app.db.mongo import alerts_col

router = APIRouter()


class AlertResolutionRequest(BaseModel):
    status: str  # "open", "closed", "false_positive", "confirmed_fraud"
    note: Optional[str] = None


@router.get("/alerts")
def list_alerts(admin: dict = Depends(get_current_admin)):
    cursor = alerts_col.find({}).sort("created_at", -1).limit(100)
    alerts = []
    for a in cursor:
        alerts.append(
            {
                "alert_id": a.get("alert_id"),
                "user_id": a.get("user_id"),
                "txn_id": a.get("txn_id"),
                "risk_level": a.get("risk_level"),
                "final_risk_score": a.get("final_risk_score"),
                "reason": a.get("reason"),
                "status": a.get("status"),
                "created_at": a.get("created_at"),
                "resolved_at": a.get("resolved_at"),
                "resolved_by": a.get("resolved_by"),
            }
        )
    return alerts


@router.patch("/alerts/{alert_id}")
def resolve_alert(
    alert_id: str,
    payload: AlertResolutionRequest,
    admin: dict = Depends(get_current_admin),
):
    alert = alerts_col.find_one({"alert_id": alert_id})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    update_doc = {
        "status": payload.status,
        "resolved_at": datetime.utcnow().isoformat(),
        "resolved_by": admin["email"],
    }
    if payload.note:
        update_doc["resolution_note"] = payload.note

    alerts_col.update_one({"alert_id": alert_id}, {"$set": update_doc})

    return {"success": True, "alert_id": alert_id, "new_status": payload.status}
