def deviation_score(current, avg, std):
    if std == 0:
        return 0
    score = abs(current - avg) / std
    return min(score, 100)
