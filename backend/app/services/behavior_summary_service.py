import os
from datetime import datetime, timedelta
from statistics import mean
from backend.app.db.mongo import txns_col, profiles_col
from backend.app.services.llm_client import LLMClient

llm = LLMClient(provider="openai")

def generate_behavior_summary(user_id: str):
    profile = profiles_col.find_one({"user_id": user_id})
    if not profile:
        return {"success": False, "message": "User profile not found"}

    cutoff_date = datetime.utcnow() - timedelta(days=30)

    txns = list(
        txns_col.find({"user_id": user_id, "timestamp": {"$gte": cutoff_date}})
        .sort("timestamp", -1)
    )

    if not txns:
        return {
            "success": True,
            "user_id": user_id,
            "summary": "No recent activity in the last 30 days.",
            "analysis": {},
        }

    # Compute aggregated stats
    final_scores = [t["ml_scores"]["final_risk_score"] for t in txns]
    anomalies = [t["ml_scores"]["anomaly_score"] for t in txns]

    avg_risk = mean(final_scores)
    max_risk = max(final_scores)
    avg_anomaly = mean(anomalies)

    risk_dist = {
        "low": sum(1 for t in txns if t["ml_scores"]["risk_level"] == "low"),
        "medium": sum(1 for t in txns if t["ml_scores"]["risk_level"] == "medium"),
        "high": sum(1 for t in txns if t["ml_scores"]["risk_level"] == "high"),
        "critical": sum(1 for t in txns if t["ml_scores"]["risk_level"] == "critical"),
    }

    prompt = f"""
You are Veritas Sentinel AI. Generate a 30-day behaviour summary for this user.

PROFILE:
- Trust Score: {profile.get("trust_score")}
- Avg Risk: {profile["risk_stats"]["avg_risk_score"]}
- High Risk Txns: {profile["risk_stats"]["high_risk_txn_count"]}

PAST 30 DAYS (Total {len(txns)} txns):
- Average Final Risk: {avg_risk}
- Maximum Final Risk: {max_risk}
- Average Anomaly Score: {avg_anomaly}
- Risk Level Distribution: {risk_dist}

TASK:
Write a professional fraud-analyst style summary covering:
1. Overall user behaviour
2. Any unusual spending or transaction spikes
3. Sudden risk score changes
4. Trust score movement
5. Notable risk patterns or red flags
6. Final behavioral verdict (normal / mildly suspicious / concerning / highly irregular)

Return ONLY valid JSON:
{
  "verdict": "<string>",
  "summary": "<multi-sentence explanation>",
  "key_patterns": ["...", "..."]
}
"""

    result = llm.generate(prompt)

    return {
        "success": True,
        "user_id": user_id,
        "summary": result
    }
