from datetime import datetime, timedelta
from statistics import mean
from backend.app.db.mongo import txns_col, profiles_col


def get_risk_trend(user_id: str):
    profile = profiles_col.find_one({"user_id": user_id})
    if not profile:
        return {"success": False, "message": "User not found"}

    # Last 30 days
    cutoff = datetime.utcnow() - timedelta(days=30)

    txns = list(
        txns_col.find({
            "user_id": user_id,
            "timestamp": {"$gte": cutoff}
        }).sort("timestamp", 1)
    )

    if not txns:
        return {
            "success": True,
            "user_id": user_id,
            "days": [],
            "message": "No transactions in last 30 days"
        }

    # Organize by day
    day_buckets = {}

    for t in txns:
        day = t["timestamp"].strftime("%Y-%m-%d")
        if day not in day_buckets:
            day_buckets[day] = {
                "risks": [],
                "anomalies": [],
                "high_risk_events": 0
            }

        day_buckets[day]["risks"].append(t["ml_scores"]["final_risk_score"])
        day_buckets[day]["anomalies"].append(t["ml_scores"]["anomaly_score"])

        if t["ml_scores"]["final_risk_score"] > 70:
            day_buckets[day]["high_risk_events"] += 1

    # Build result timeline
    timeline = []
    trust_score = profile.get("trust_score", 100)

    # OPTIONAL: trust score decay per day (simulated while no actual model)
    trust_drop_rate = 0.1  

    for day, values in day_buckets.items():
        avg_risk = mean(values["risks"])
        max_risk = max(values["risks"])
        avg_anomaly = mean(values["anomalies"])

        timeline.append({
            "date": day,
            "avg_risk": round(avg_risk, 3),
            "max_risk": round(max_risk, 3),
            "avg_anomaly": round(avg_anomaly, 3),
            "trust_score": round(trust_score, 2),
            "high_risk_events": values["high_risk_events"]
        })

        trust_score -= trust_drop_rate

    return {
        "success": True,
        "user_id": user_id,
        "days": timeline
    }
