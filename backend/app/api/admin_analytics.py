# backend/app/api/admin_analytics.py

from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import APIRouter, Depends

from backend.app.core.security import get_current_admin
from backend.app.db.mongo import txns_col

router = APIRouter()


@router.get("/risk-trend-global")
def global_risk_trend(days: int = 30, admin: dict = Depends(get_current_admin)) -> Dict[str, Any]:
    """
    Admin-only: global risk trend over the last N days across ALL users.
    Returns a list of daily aggregates suitable for graphs.
    """

    cutoff = datetime.utcnow() - timedelta(days=days)
    cutoff_iso = cutoff.isoformat()

    # Fetch last N days of transactions
    raw_txns: List[dict] = list(
        txns_col.find({"timestamp": {"$gte": cutoff_iso}})
        .sort("timestamp", 1)
    )

    buckets: Dict[str, dict] = {}

    for t in raw_txns:
        ts_raw = t.get("timestamp")
        try:
            ts = datetime.fromisoformat(ts_raw) if isinstance(ts_raw, str) else ts_raw
        except Exception:
            continue

        day = ts.strftime("%Y-%m-%d")
        if day not in buckets:
            buckets[day] = {
                "total_txns": 0,
                "total_risk": 0.0,
                "total_fraud_prob": 0.0,
                "alert_like_events": 0,
                "users": set(),
            }

        ml = t.get("ml_scores", {}) or {}
        risk = float(ml.get("final_risk_score", 0.0))
        fraud_prob = float(ml.get("fraud_probability", 0.0))
        risk_level = ml.get("risk_level", "low")

        buckets[day]["total_txns"] += 1
        buckets[day]["total_risk"] += risk
        buckets[day]["total_fraud_prob"] += fraud_prob
        buckets[day]["users"].add(t.get("user_id"))

        if risk_level in ["high", "critical"]:
            buckets[day]["alert_like_events"] += 1

    timeline = []
    for day in sorted(buckets.keys()):
        b = buckets[day]
        avg_risk = b["total_risk"] / b["total_txns"]
        avg_fraud_prob = b["total_fraud_prob"] / b["total_txns"]

        timeline.append({
            "date": day,
            "total_txns": b["total_txns"],
            "avg_risk": round(avg_risk, 2),
            "avg_fraud_probability": round(avg_fraud_prob, 2),
            "high_risk_events": b["alert_like_events"],
            "unique_users": len(b["users"]),
        })

    return {
        "success": True,
        "days": timeline,
    }


@router.get("/geo-hotspots")
def geo_hotspots(days: int = 30, admin: dict = Depends(get_current_admin)):
    """
    Admin-only: geo risk hotspots based on transaction locations.

    Returns list of points:
    - country, city
    - lat, lon
    - txn_count
    - high_risk_count
    - avg_risk
    - avg_fraud_probability
    """

    cutoff = datetime.utcnow() - timedelta(days=days)
    cutoff_iso = cutoff.isoformat()

    raw_txns = list(
        txns_col.find({
            "timestamp": {"$gte": cutoff_iso},
            "location": {"$ne": None}
        }).sort("timestamp", 1)
    )

    buckets: Dict[str, dict] = {}

    for t in raw_txns:
        loc = t.get("location") or {}
        country = (loc.get("country") or "").strip()
        city = (loc.get("city") or "").strip()
        lat = loc.get("lat")
        lon = loc.get("lon")

        if not country or lat is None or lon is None:
            continue

        ml = t.get("ml_scores", {}) or {}
        risk = float(ml.get("final_risk_score", 0.0))
        fraud_prob = float(ml.get("fraud_probability", 0.0))
        risk_level = ml.get("risk_level", "low")

        key = f"{country}::{city}"

        if key not in buckets:
            buckets[key] = {
                "country": country,
                "city": city or None,
                "lat": lat,
                "lon": lon,
                "txn_count": 0,
                "high_risk_count": 0,
                "total_risk": 0.0,
                "total_fraud_prob": 0.0,
            }

        b = buckets[key]
        b["txn_count"] += 1
        b["total_risk"] += risk
        b["total_fraud_prob"] += fraud_prob
        if risk_level in ["high", "critical"]:
            b["high_risk_count"] += 1

    hotspots = []
    for key, b in buckets.items():
        if b["txn_count"] == 0:
            continue

        avg_risk = b["total_risk"] / b["txn_count"]
        avg_fraud = b["total_fraud_prob"] / b["txn_count"]

        hotspots.append({
            "country": b["country"],
            "city": b["city"],
            "lat": b["lat"],
            "lon": b["lon"],
            "txn_count": b["txn_count"],
            "high_risk_count": b["high_risk_count"],
            "avg_risk": round(avg_risk, 2),
            "avg_fraud_probability": round(avg_fraud, 2),
        })

    return {
        "success": True,
        "points": hotspots,
    }
