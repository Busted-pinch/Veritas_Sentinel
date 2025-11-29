# backend/app/api/transactions.py
from fastapi import APIRouter, HTTPException
from datetime import datetime
from numbers import Number
import uuid

from backend.app.db.mongo import txns_col, alerts_col
from backend.app.db.models.transaction import TransactionCreate
from backend.app.services.profile_service import get_or_create_profile, update_profile_with_transaction
from backend.app.services.feature_builder import build_features_from_transaction
from backend.app.ml.predictor import predict_transaction

router = APIRouter()

def _sanitize_scores(scores: dict) -> dict:
    clean = {}
    for k, v in scores.items():
        if isinstance(v, Number):
            clean[k] = float(v)
        else:
            clean[k] = v
    return clean


@router.post("/transaction/new")
def create_transaction(txn: TransactionCreate):
    # 1. Ensure timestamp
    ts = txn.timestamp or datetime.utcnow().isoformat()

    # 2. Build features (step, amount, isFlaggedFraud)
    features = build_features_from_transaction(txn)

    # 3. Get or create user profile
    profile = get_or_create_profile(txn.user_id)

    # 4. Run ML risk engine
    try:
        risk_result_raw = predict_transaction(features, profile)
        risk_result = _sanitize_scores(risk_result_raw)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    final_risk = risk_result["final_risk_score"]
    risk_level = risk_result["risk_level"]

    # 5. Generate txn_id
    txn_id = f"T-{uuid.uuid4().hex[:12]}"

    # 6. Prepare document for DB
    txn_doc = {
        "txn_id": txn_id,
        "user_id": txn.user_id,
        "amount": txn.amount,
        "currency": txn.currency,
        "channel": txn.channel,
        "merchant_type": txn.merchant_type,
        "location": txn.location.dict() if txn.location else None,
        "device": txn.device.dict() if txn.device else None,
        "timestamp": ts,
        "ml_scores": risk_result,
        "label": None,
        "status": "normal",   # can be changed later by analyst
        "created_at": datetime.utcnow().isoformat()
    }

    txns_col.insert_one(txn_doc)

    # 7. Update user profile stats (amount + risk, trust)
    updated_profile = update_profile_with_transaction(
        user_id=txn.user_id,
        amount=txn.amount,
        final_risk_score=final_risk
    )

    # 8. Create alert if high or critical
    alert_id = None
    if risk_level in ["high", "critical"]:
        alert_id = f"A-{uuid.uuid4().hex[:12]}"
        alerts_col.insert_one({
            "alert_id": alert_id,
            "txn_id": txn_id,
            "user_id": txn.user_id,
            "risk_level": risk_level,
            "final_risk_score": final_risk,
            "reason": _build_alert_reason(risk_result),
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
            "resolved_at": None,
            "resolved_by": None,
            "resolution_note": None
        })

    return {
        "success": True,
        "txn_id": txn_id,
        "user_id": txn.user_id,
        "ml_scores": risk_result,
        "risk_alert_id": alert_id,
        "risk_level": risk_level,
        "updated_profile": {
            "trust_score": updated_profile["trust_score"],
            "avg_risk_score": updated_profile["risk_stats"]["avg_risk_score"],
            "high_risk_txn_count": updated_profile["risk_stats"]["high_risk_txn_count"],
            "total_txn_count": updated_profile["risk_stats"]["total_txn_count"]
        }
    }


def _build_alert_reason(risk_result: dict):
    """
    Create a human-readable list of reasons for the alert.
    Very simple version for now.
    """
    reasons = []

    if risk_result["fraud_probability"] >= 70:
        reasons.append("High fraud probability from supervised model")

    if risk_result["anomaly_score"] >= 60:
        reasons.append("Unusual transaction pattern detected (anomaly)")

    if risk_result["deviation_score"] >= 50:
        reasons.append("Transaction amount deviates strongly from user history")

    if risk_result["trust_score"] <= 40:
        reasons.append("User has low trust score based on past behaviour")

    if not reasons:
        reasons.append("Combined risk score exceeded threshold")

    return reasons
