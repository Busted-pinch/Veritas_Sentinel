def compute_trust(profile):
    score = 100
    score -= profile.get("avg_risk", 0) * 0.4
    score -= profile.get("anomaly_freq", 0) * 0.3
    score -= profile.get("device_change_rate", 0) * 0.2
    score = max(0, min(100, score))
    return score
