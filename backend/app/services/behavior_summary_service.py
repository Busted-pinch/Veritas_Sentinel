# backend/app/services/behavior_summary_service.py

from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Dict, Any

from backend.app.db.mongo import txns_col, profiles_col
from backend.app.services.llm_client import LLMClient

llm = LLMClient(provider="openai")


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def generate_behavior_summary(user_id: str) -> Dict[str, Any]:
    profile = profiles_col.find_one({"user_id": user_id})
    if not profile:
        return {"success": False, "message": "User profile not found"}

    raw_txns = list(
        txns_col.find({"user_id": user_id}).sort("timestamp", -1).limit(100)
    )

    cutoff = _to_utc(datetime.utcnow()) - timedelta(days=30)
    txns = []

    for t in raw_txns:
        ts_raw = t.get("timestamp")

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

        if ts_utc >= cutoff:
            txns.append(t)

    if not txns:
        return {
            "success": True,
            "user_id": user_id,
            "summary": "No recent activity in the last 30 days.",
            "analysis": {},
        }

    final_scores = [t["ml_scores"]["final_risk_score"] for t in txns]
    anomalies = [t["ml_scores"]["anomaly_score"] for t in txns]

    avg_risk = mean(final_scores)
    max_risk = max(final_scores)
    avg_anomaly = mean(anomalies)

    risk_dist = {
        "low": sum(1 for t in txns if t["ml_scores"]["risk_level"] == "low"),
        "medium": sum(1 for t in txns if t["ml_scores"]["risk_level"] == "medium"),
        "high": sum(1 for t in txns if t["ml_scores"]["risk_level"] == "high"),
        "critical": sum(
            1 for t in txns if t["ml_scores"]["risk_level"] == "critical"
        ),
    }

    prompt = f"""
You are Veritas Sentinel AI. Generate a 30-day behaviour summary for this user.

PROFILE:
- Trust Score: {profile.get("trust_score")}
- Avg Risk (lifetime): {profile["risk_stats"]["avg_risk_score"]}
- High Risk Txns (lifetime): {profile["risk_stats"]["high_risk_txn_count"]}
- Total Txns (lifetime): {profile["risk_stats"]["total_txn_count"]}

PAST 30 DAYS (Total {len(txns)} txns):
- Average Final Risk (30d): {avg_risk}
- Maximum Final Risk (30d): {max_risk}
- Average Anomaly Score (30d): {avg_anomaly}
- Risk Level Distribution (30d): {risk_dist}

TASK:
Write a professional fraud-analyst style summary covering:
1. Overall user behaviour
2. Any unusual spending or transaction spikes
3. Sudden risk score changes
4. Trust score movement if implied
5. Notable risk patterns or red flags
6. Final behavioral verdict (normal / mildly suspicious / concerning / highly irregular)

Return ONLY valid JSON:
{{
  "verdict": "<string>",
  "summary": "<multi-sentence explanation>",
  "key_patterns": ["...", "..."]
}}
"""

    llm_json = llm.generate(prompt)

    return {
        "success": True,
        "user_id": user_id,
        "summary": llm_json,
    }
