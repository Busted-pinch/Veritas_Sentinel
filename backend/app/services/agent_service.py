import os
from statistics import mean
from backend.app.db.mongo import txns_col, profiles_col
from backend.app.services.llm_client import LLMClient


llm = LLMClient(provider=os.getenv("LLM_PROVIDER", "openai"))


def speculate_user(user_id: str):
    profile = profiles_col.find_one({"user_id": user_id})
    if not profile:
        return {"success": False, "message": "User profile not found."}

    # Fetch last 20 transactions
    txns = list(
        txns_col.find({"user_id": user_id})
        .sort("timestamp", -1)
        .limit(20)
    )

    if not txns:
        return {
            "success": True,
            "user_id": user_id,
            "agent_result": {
                "speculation_score": 0,
                "risk_level": "low",
                "explanation": "No transactions available to analyze.",
                "indicators": []
            }
        }

    # Extract structured metrics
    final_scores = [t["ml_scores"]["final_risk_score"] for t in txns]
    fraud_probs = [t["ml_scores"]["fraud_probability"] for t in txns]
    anomalies = [t["ml_scores"]["anomaly_score"] for t in txns]

    risk_level_counts = {
        "low": sum(1 for t in txns if t["ml_scores"]["risk_level"] == "low"),
        "medium": sum(1 for t in txns if t["ml_scores"]["risk_level"] == "medium"),
        "high": sum(1 for t in txns if t["ml_scores"]["risk_level"] == "high"),
        "critical": sum(1 for t in txns if t["ml_scores"]["risk_level"] == "critical"),
    }

    # Build LLM prompt
    prompt = f"""
You are Veritas Sentinel AI — a fraud-risk speculation agent.

Analyze the user's behavior and produce:
- a speculation_score (0 to 100)
- a risk_level (low / medium / high / critical)
- a narrative explanation (3–6 sentences)
- a list of key indicators

USER PROFILE:
- Trust Score: {profile.get("trust_score")}
- Avg Risk: {profile['risk_stats']['avg_risk_score']}
- High-risk Txns: {profile['risk_stats']['high_risk_txn_count']}
- Total Txns: {profile['risk_stats']['total_txn_count']}

RECENT TRANSACTIONS (Last {len(txns)}):
- Avg Final Risk: {mean(final_scores)}
- Max Final Risk: {max(final_scores)}
- Avg Fraud Probability: {mean(fraud_probs)}
- Avg Anomaly Score: {mean(anomalies)}
- Risk Levels: {risk_level_counts}

Return ONLY valid JSON in the structure:
{
  "speculation_score": <number>,
  "risk_level": "<string>",
  "explanation": "<string>",
  "indicators": ["...", "..."]
}
"""

    try:
        llm_output = llm.generate(prompt)
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {
        "success": True,
        "user_id": user_id,
        "agent_result": llm_output
    }
