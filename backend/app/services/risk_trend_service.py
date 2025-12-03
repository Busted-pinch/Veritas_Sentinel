# backend/app/services/risk_trend_service.py

from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Dict, Any, List

from backend.app.db.mongo import txns_col, profiles_col


def _to_utc(dt: datetime) -> datetime:
    """
    Ensure a datetime is timezone-aware in UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_risk_trend(user_id: str) -> Dict[str, Any]:
    """
    Build a 30-day risk/anomaly/trust timeline for a user.
    Never throws on weird timestamps – just skips bad rows and
    returns a clean JSON dict the frontend can always parse.
    """
    profile = profiles_col.find_one({"user_id": user_id})
    if not profile:
        return {"success": False, "message": "User not found"}

    # Pull last ~200 txns, then filter by last 30 days in Python.
    raw_txns = list(
        txns_col.find({"user_id": user_id}).sort("timestamp", 1).limit(200)
    )

    cutoff = _to_utc(datetime.utcnow()) - timedelta(days=30)
    txns: List[dict] = []

    for t in raw_txns:
        ts_raw = t.get("timestamp")

        # Support both string ISO and native datetime from Mongo
        if isinstance(ts_raw, str):
            try:
                ts = datetime.fromisoformat(ts_raw)
            except Exception:
                continue
        elif isinstance(ts_raw, datetime):
            ts = ts_raw
        else:
            continue

        ts_utc = _to_utc(ts)

        # This is the line that previously crashed (naive vs aware)
        if ts_utc >= cutoff:
            t["_parsed_ts"] = ts_utc
            txns.append(t)

    if not txns:
        return {
            "success": True,
            "user_id": user_id,
            "days": [],
            "message": "No transactions in the last 30 days",
        }

    day_buckets: Dict[str, dict] = {}

    for t in txns:
        ts: datetime = t["_parsed_ts"]
        day = ts.strftime("%Y-%m-%d")
        if day not in day_buckets:
            day_buckets[day] = {
                "risks": [],
                "anomalies": [],
                "high_risk_events": 0,
            }

        ml_scores = t.get("ml_scores") or {}
        score = ml_scores.get("final_risk_score")
        anomaly = ml_scores.get("anomaly_score")

        # skip if scores missing / malformed
        if score is None or anomaly is None:
            continue

        score = float(score)
        anomaly = float(anomaly)

        day_buckets[day]["risks"].append(score)
        day_buckets[day]["anomalies"].append(anomaly)
        if score > 70:
            day_buckets[day]["high_risk_events"] += 1

    trust_score = float(profile.get("trust_score", 100.0))

    timeline = []
    for day in sorted(day_buckets.keys()):
        values = day_buckets[day]
        if not values["risks"]:
            continue

        avg_risk = mean(values["risks"])
        max_risk = max(values["risks"])
        avg_anomaly = mean(values["anomalies"])

        timeline.append(
            {
                "date": day,
                "avg_risk": round(avg_risk, 2),
                "max_risk": round(max_risk, 2),
                "avg_anomaly": round(avg_anomaly, 2),
                "trust_score": round(trust_score, 2),
                "high_risk_events": values["high_risk_events"],
            }
        )

    return {
        "success": True,
        "user_id": user_id,
        "days": timeline,
    }
