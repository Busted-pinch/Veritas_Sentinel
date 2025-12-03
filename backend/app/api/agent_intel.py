# backend/app/api/agent_intel.py

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.app.core.security import get_current_admin
from backend.app.db.mongo import profiles_col, txns_col, alerts_col
from backend.app.services.agent_service import speculate_user
from backend.app.services.behavior_summary_service import generate_behavior_summary
from backend.app.services.investigation_service import generate_case_file
from backend.app.services.risk_trend_service import get_risk_trend


router = APIRouter()


class IntelRequest(BaseModel):
    user_id: str


def _parse_json_maybe(value: Any) -> Any:
    """
    Try to parse a JSON string into a dict; if it fails, return the original value.
    This is for LLM outputs which come back as strings.
    """
    if isinstance(value, (dict, list)) or value is None:
        return value
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


def _clean_profile(profile: Optional[Dict]) -> Optional[Dict]:
    if not profile:
        return None

    return {
        "user_id": profile.get("user_id"),
        "trust_score": profile.get("trust_score"),
        "amount_stats": profile.get("amount_stats"),
        "risk_stats": profile.get("risk_stats"),
        "updated_at": profile.get("updated_at"),
        "created_at": profile.get("created_at"),
    }


def _clean_transactions(txns: List[Dict]) -> List[Dict]:
    cleaned = []
    for t in txns:
        ml = t.get("ml_scores", {}) or {}
        cleaned.append({
            "txn_id": t.get("txn_id"),
            "timestamp": t.get("timestamp"),
            "amount": t.get("amount"),
            "currency": t.get("currency"),
            "channel": t.get("channel"),
            "merchant_type": t.get("merchant_type"),
            "risk_level": ml.get("risk_level"),
            "final_risk_score": ml.get("final_risk_score"),
            "fraud_probability": ml.get("fraud_probability"),
            "anomaly_score": ml.get("anomaly_score"),
            "deviation_score": ml.get("deviation_score"),
        })
    return cleaned


def _clean_alerts(alerts: List[Dict]) -> List[Dict]:
    cleaned = []
    for a in alerts:
        cleaned.append({
            "alert_id": a.get("alert_id"),
            "txn_id": a.get("txn_id"),
            "user_code": a.get("user_code"),
            "risk_level": a.get("risk_level"),
            "final_risk_score": a.get("final_risk_score"),
            "reason": a.get("reason"),
            "status": a.get("status"),
            "created_at": a.get("created_at"),
            "resolved_at": a.get("resolved_at"),
            "resolved_by": a.get("resolved_by"),
        })
    return cleaned



@router.post("/intel")
def user_intelligence(req: IntelRequest, admin: dict = Depends(get_current_admin)):
    """
    Admin-only: unified, CLEAN intelligence endpoint for a user.

    Returns:
    - profile (trust + stats)
    - compact recent transactions (last 20)
    - compact alerts (last 20)
    - 30-day risk trend (days[])
    - speculation summary (LLM)
    - behaviour summary (LLM)
    - investigation case file (LLM)
    """

    user_id = req.user_id

    # --- Core data from Mongo ---
    profile = profiles_col.find_one({"user_id": user_id})
    clean_profile = _clean_profile(profile)

    raw_txns = list(
        txns_col.find({"user_id": user_id})
        .sort("timestamp", -1)
        .limit(20)
    )
    clean_txns = _clean_transactions(raw_txns)

    raw_alerts = list(
        alerts_col.find({"user_id": user_id})
        .sort("created_at", -1)
        .limit(20)
    )
    clean_alerts = _clean_alerts(raw_alerts)

    # --- Agent services (reuse existing logic) ---
    speculation = speculate_user(user_id)
    behaviour = generate_behavior_summary(user_id)
    investigation = generate_case_file(user_id)
    trend = get_risk_trend(user_id)

    # Parse LLM JSON fields where possible
    spec_parsed = _parse_json_maybe(speculation.get("agent_result")) if isinstance(speculation, dict) else speculation
    behaviour_parsed = _parse_json_maybe(behaviour.get("summary")) if isinstance(behaviour, dict) else behaviour
    investigation_parsed = _parse_json_maybe(investigation.get("case_file")) if isinstance(investigation, dict) else investigation

    # Risk trend days list
    trend_days = trend.get("days", []) if isinstance(trend, dict) else []

    # Simple metrics summary
    metrics = {
        "recent_txn_count": len(clean_txns),
        "alert_count": len(clean_alerts),
        "has_profile": clean_profile is not None,
    }

    return {
        "success": True,
        "user_id": user_id,
        "profile": clean_profile,
        "metrics": metrics,
        "summary": {
            "behaviour": behaviour_parsed,
            "investigation": investigation_parsed,
            "speculation": spec_parsed,
        },
        "trend_30d": trend_days,
        "recent_transactions": clean_txns,
        "alerts": clean_alerts,
    }
