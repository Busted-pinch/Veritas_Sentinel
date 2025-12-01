import os
from datetime import datetime, timedelta
from statistics import mean
from backend.app.db.mongo import txns_col, profiles_col
from backend.app.services.llm_client import LLMClient

llm = LLMClient(provider="openai")

def generate_case_file(user_id: str):
    profile = profiles_col.find_one({"user_id": user_id})
    if not profile:
        return {"success": False, "message": "User profile not found"}

    txns = list(
        txns_col.find({"user_id": user_id}).sort("timestamp", -1)
    )

    if not txns:
        return {"success": True, "user_id": user_id, "case_file": "No transaction history available."}

    risks = [t["ml_scores"]["final_risk_score"] for t in txns]
    anomalies = [t["ml_scores"]["anomaly_score"] for t in txns]

    avg_risk = mean(risks)
    max_risk = max(risks)
    avg_anomaly = mean(anomalies)

    recent_high_risk = [
        t for t in txns if t["ml_scores"]["final_risk_score"] > 70
    ]

    prompt = f"""
You are Veritas Sentinel AI. Generate a full fraud investigation case file.

USER PROFILE:
- User ID: {user_id}
- Trust Score: {profile.get("trust_score")}
- Avg Risk: {profile["risk_stats"]["avg_risk_score"]}
- High Risk Txn Count: {profile["risk_stats"]["high_risk_txn_count"]}
- Total Txns: {profile["risk_stats"]["total_txn_count"]}

AGGREGATED ANALYSIS:
- Average Final Risk: {avg_risk}
- Maximum Final Risk: {max_risk}
- Average Anomaly Score: {avg_anomaly}
- Recent High-Risk Transaction Count: {len(recent_high_risk)}

TASK:
Produce a detailed case file including:
1. Executive summary (2–4 sentences)
2. User risk profile assessment
3. Transaction anomalies timeline
4. Behavioral red flags
5. Indicators supporting fraud suspicion
6. Final recommended action:
   - "Block"
   - "Flag for manual review"
   - "Place under monitoring"
   - or "No action needed"

Return ONLY JSON:
{
  "executive_summary": "<string>",
  "risk_rating": "<low / medium / high / critical>",
  "behaviour_findings": ["...", "..."],
  "anomaly_timeline": ["...", "..."],
  "recommended_action": "<string>"
}
"""

    result = llm.generate(prompt)

    return {
        "success": True,
        "user_id": user_id,
        "case_file": result
    }
