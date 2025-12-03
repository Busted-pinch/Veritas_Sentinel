# backend/app/api/transactions.py

from datetime import datetime
from typing import Dict, Any, Union

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from backend.app.core.security import get_current_user
from backend.app.db.mongo import txns_col, alerts_col
from backend.app.db.models.transaction import TransactionCreate
from backend.app.ml.engine import TransactionEngine
from backend.app.services.feature_builder import build_features_from_transaction
from backend.app.services.profile_service import (
    get_or_create_profile,
    update_profile_with_transaction,
)
from backend.app.services.rules_service import evaluate_rules_for_transaction
from backend.app.services.risk_trend_service import get_risk_trend

router = APIRouter()
engine = TransactionEngine()


def _strip_object_ids(obj: Any) -> Any:
    """
    Recursively:
    - remove '_id' keys
    - convert bson.ObjectId to str
    so Pydantic / JSON encoding never sees raw ObjectIds.
    """
    if isinstance(obj, ObjectId):
        return str(obj)

    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            if k == "_id":
                continue
            cleaned[k] = _strip_object_ids(v)
        return cleaned

    if isinstance(obj, list):
        return [_strip_object_ids(v) for v in obj]

    return obj


@router.post("/transaction/new", response_model=Dict[str, Any])
def create_transaction(
    txn: TransactionCreate, current_user: dict = Depends(get_current_user)
):
    """
    User-facing endpoint: submit a transaction for risk analysis.
    - Forces user_id from auth token (ignores any spoofed body value)
    - Runs rules + ML engine
    - Updates profile stats
    - Optionally creates an alert
    """
    user_id = current_user["user_id"]

    # ---- Normalise txn_type for balance semantics ----
    raw_type = (txn.txn_type or "WITHDRAW").upper()
    if raw_type not in ("DEPOSIT", "WITHDRAW"):
        raw_type = "WITHDRAW"

    # ---- Build base features (without rules) ----
    feature_dict = build_features_from_transaction(txn)

    # ---- Get profile (or create default) ----
    profile = get_or_create_profile(user_id)

    # ---- Rules evaluation (txn + profile) ----
    rules_result = evaluate_rules_for_transaction(txn, profile)
    is_flagged = int(rules_result.get("isFlaggedFraud", 0))

    # Sync rules flag into ML features
    feature_dict["isFlaggedFraud"] = is_flagged

    # ---- ML prediction ----
    ml_scores = engine.predict_transaction(feature_dict, profile)
    ml_scores["is_flagged_by_rules"] = bool(is_flagged)

    # ---- Update profile with this txn (amount, risk) ----
    updated_profile = update_profile_with_transaction(
        user_id=user_id,
        amount=txn.amount,
        final_risk_score=ml_scores["final_risk_score"],
    )

    # ---- Persist transaction ----
    txn_id = f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    timestamp = txn.timestamp or datetime.utcnow().isoformat()

    txn_doc: Dict[str, Any] = {
        "txn_id": txn_id,
        "user_id": user_id,
        "amount": txn.amount,
        "channel": txn.channel,
        "currency": txn.currency or "INR",
        "merchant_type": txn.merchant_type,
        "location": txn.location.dict() if txn.location else None,
        "device": txn.device.dict() if txn.device else None,
        "timestamp": timestamp,
        "ml_scores": ml_scores,
        "rules": rules_result,
        "txn_type": raw_type,
        "created_at": datetime.utcnow().isoformat(),
    }

    txns_col.insert_one(txn_doc)

    # ---- Alert decision (tighter than “anything non-low”) ----
    risk_level = ml_scores["risk_level"]
    final_score = ml_scores["final_risk_score"]
    fraud_prob = ml_scores["fraud_probability"]

    should_alert = False
    if risk_level in ("high", "critical"):
        should_alert = True
    elif risk_level == "medium" and (final_score >= 65 or fraud_prob >= 70):
        should_alert = True
    elif is_flagged and final_score >= 55:
        should_alert = True

    alert_doc: Union[Dict[str, Any], None] = None
    if should_alert:
        alert_id = f"ALERT-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        alert_doc = {
            "alert_id": alert_id,
            "user_id": user_id,
            "user_code": current_user.get("user_code"),
            "txn_id": txn_id,
            "risk_level": risk_level,
            "final_risk_score": final_score,
            "fraud_probability": fraud_prob,
            "rules_triggered": rules_result.get("matched_rules", []),
            "status": "open",
            "note": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "reason": _build_alert_reason(txn_doc, ml_scores, rules_result),
        }
        alerts_col.insert_one(alert_doc)

    # ---- Clean profile for frontend (just the key stats) ----
    clean_profile = {
        "user_id": updated_profile["user_id"],
        "trust_score": updated_profile.get("trust_score", 100.0),
        "amount_stats": updated_profile.get("amount_stats", {}),
        "risk_stats": updated_profile.get("risk_stats", {}),
    }

    response = {
        "success": True,
        "txn_id": txn_id,
        "user_id": user_id,
        "txn_type": raw_type,
        "ml_scores": ml_scores,
        "rules": rules_result,
        "profile": clean_profile,
        "alert_created": bool(alert_doc),
        "alert": alert_doc,
    }

    return _strip_object_ids(response)


def _build_alert_reason(
    txn_doc: Dict[str, Any], ml_scores: Dict[str, Any], rules_result: Dict[str, Any]
) -> str:
    """
    Explain *why* an alert exists in plain English.
    """
    parts = []
    amount = float(txn_doc["amount"])
    risk_level = ml_scores["risk_level"]
    final_score = float(ml_scores["final_risk_score"])
    fraud_prob = float(ml_scores["fraud_probability"])

    parts.append(
        f"Transaction of ₹{amount:.2f} was scored as {risk_level.upper()} risk "
        f"(final risk score {final_score:.1f}, fraud probability {fraud_prob:.1f}%)."
    )

    matched = rules_result.get("matched_rules", [])
    if matched:
        # matched is a list of strings like ["R1_VERY_HIGH_AMOUNT", ...]
        rule_names = ", ".join(str(r) for r in matched)
        parts.append(f"Triggered rules: {rule_names}.")

    if fraud_prob >= 85:
        parts.append(
            "Very high estimated fraud probability based on amount, deviation from normal behaviour, and trust score."
        )
    elif fraud_prob >= 70:
        parts.append(
            "Elevated fraud probability compared to this user's historical behaviour."
        )

    anomaly_score = float(ml_scores.get("anomaly_score", 0))
    if anomaly_score >= 70:
        parts.append(
            "Transaction appears highly anomalous relative to the user's historical pattern."
        )

    return " ".join(parts).strip()


# ---------- USER SELF-SERVICE ENDPOINTS ----------

@router.get("/transactions/me/summary")
def my_summary(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    For the logged-in user:
    - Current balance (computed from DEPOSIT / WITHDRAW)
    - Lifetime profile stats (avg risk, high-risk count, etc.)
    """
    user_id = current_user["user_id"]

    txns = list(txns_col.find({"user_id": user_id}).sort("timestamp", -1))

    balance = 0.0
    for t in txns:
        ttype = (t.get("txn_type") or "WITHDRAW").upper()
        amt = float(t.get("amount", 0) or 0)
        if ttype in ("DEPOSIT", "CREDIT"):
            balance += amt
        else:
            balance -= amt

    profile = get_or_create_profile(user_id)

    clean_profile = {
        "user_id": profile["user_id"],
        "trust_score": profile.get("trust_score", 100.0),
        "amount_stats": profile.get("amount_stats", {}),
        "risk_stats": profile.get("risk_stats", {}),
    }

    return {
        "success": True,
        "user_id": user_id,
        "balance": round(balance, 2),
        "profile": clean_profile,
    }


@router.get("/transactions/me/risk-trend")
def my_risk_trend(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Same 30-day risk trend as admin has, but for the logged-in user only.
    """
    user_id = current_user["user_id"]
    return get_risk_trend(user_id)


@router.get("/transactions/me/history")
def my_history(
    limit: int = 10, current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Recent N transactions for the logged-in user.
    """
    user_id = current_user["user_id"]
    limit = max(1, min(limit, 50))

    txns = list(
        txns_col.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
    )

    items = []
    for t in txns:
        scores = t.get("ml_scores", {}) or {}
        items.append(
            {
                "txn_id": t.get("txn_id"),
                "amount": t.get("amount"),
                "currency": t.get("currency", "INR"),
                "channel": t.get("channel"),
                "merchant_type": t.get("merchant_type"),
                "txn_type": t.get("txn_type", "WITHDRAW"),
                "risk_level": scores.get("risk_level"),
                "final_risk_score": scores.get("final_risk_score"),
                "fraud_probability": scores.get("fraud_probability"),
                "timestamp": t.get("timestamp"),
            }
        )

    return {"success": True, "transactions": items}


@router.get("/transactions/me/alerts")
def my_alerts(
    limit: int = 10, current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Alerts *about this user*, visible to the user themselves.
    """
    user_id = current_user["user_id"]
    limit = max(1, min(limit, 50))

    raw_alerts = list(
        alerts_col.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
    )

    alerts = []
    for a in raw_alerts:
        alerts.append(
            {
                "alert_id": a.get("alert_id"),
                "risk_level": a.get("risk_level"),
                "final_risk_score": a.get("final_risk_score"),
                "fraud_probability": a.get("fraud_probability"),
                "status": a.get("status"),
                "created_at": a.get("created_at"),
                "reason": a.get("reason"),
            }
        )

    return {"success": True, "alerts": alerts}
