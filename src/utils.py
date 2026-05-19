# =========================================
# LEVEL GROUPING
# =========================================


def get_level(avg_elo: int) -> int:
    if avg_elo < 1000:
        return 2
    if avg_elo < 1200:
        return 3
    if avg_elo < 1400:
        return 4
    if avg_elo < 1600:
        return 5
    if avg_elo < 1800:
        return 6
    if avg_elo < 2000:
        return 7
    if avg_elo < 2200:
        return 8
    if avg_elo < 2400:
        return 9
    return 10
