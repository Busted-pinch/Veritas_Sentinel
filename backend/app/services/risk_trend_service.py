# backend/app/services/risk_trend_service.py

from datetime import datetime, timedelta
from statistics import mean
from typing import Dict, Any, List

from backend.app.db.mongo import txns_col, profiles_col


def get_risk_trend(user_id: str) -> Dict[str, Any]:
    profile = profiles_col.find_one({"user_id": user_id})
    if not profile:
        return {"success": False, "message": "User not found"}

    # Pull last ~200 txns, then filter by last 30 days in Python.
    raw_txns = list(
        txns_col.find({"user_id": user_id}).sort("timestamp", 1).limit(200)
    )

    cutoff = datetime.utcnow() - timedelta(days=30)
    txns: List[dict] = []
    for t in raw_txns:
        ts_raw = t.get("timestamp")
        try:
            ts = datetime.fromisoformat(ts_raw) if isinstance(ts_raw, str) else ts_raw
        except Exception:
            continue
        if ts >= cutoff:
            t["_parsed_ts"] = ts
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

        score = t["ml_scores"]["final_risk_score"]
        anomaly = t["ml_scores"]["anomaly_score"]

        day_buckets[day]["risks"].append(score)
        day_buckets[day]["anomalies"].append(anomaly)
        if score > 70:
            day_buckets[day]["high_risk_events"] += 1

    # Trust score from profile as baseline, just carried along for display
    trust_score = float(profile.get("trust_score", 100.0))

    timeline = []
    # sort by date ascending
    for day in sorted(day_buckets.keys()):
        values = day_buckets[day]
        avg_risk = mean(values["risks"])
        max_risk = max(values["risks"])
        avg_anomaly = mean(values["anomalies"])

        timeline.append({
            "date": day,
            "avg_risk": round(avg_risk, 2),
            "max_risk": round(max_risk, 2),
            "avg_anomaly": round(avg_anomaly, 2),
            "trust_score": round(trust_score, 2),
            "high_risk_events": values["high_risk_events"],
        })

    return {
        "success": True,
        "user_id": user_id,
        "days": timeline,
    }
