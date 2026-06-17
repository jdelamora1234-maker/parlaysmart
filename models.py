import math
import random

def poisson_prob(lam, k):
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

def poisson_probabilities(lambda_home, lambda_away, max_goals=7):
    matrix = [[poisson_prob(lambda_home, i) * poisson_prob(lambda_away, j)
               for j in range(max_goals)] for i in range(max_goals)]
    home_win = sum(matrix[i][j] for i in range(max_goals) for j in range(max_goals) if i > j)
    draw     = sum(matrix[i][j] for i in range(max_goals) for j in range(max_goals) if i == j)
    away_win = sum(matrix[i][j] for i in range(max_goals) for j in range(max_goals) if i < j)
    over25   = sum(matrix[i][j] for i in range(max_goals) for j in range(max_goals) if i + j > 2)
    under25  = 1 - over25
    btts     = sum(matrix[i][j] for i in range(1, max_goals) for j in range(1, max_goals))
    over35   = sum(matrix[i][j] for i in range(max_goals) for j in range(max_goals) if i + j > 3)
    return {
        "home_win": round(home_win * 100, 1),
        "draw":     round(draw     * 100, 1),
        "away_win": round(away_win * 100, 1),
        "over_2_5": round(over25   * 100, 1),
        "under_2_5":round(under25  * 100, 1),
        "btts":     round(btts     * 100, 1),
        "over_3_5": round(over35   * 100, 1),
        "expected_home_goals": round(lambda_home, 2),
        "expected_away_goals": round(lambda_away, 2),
        "most_likely_score": _most_likely_score(matrix, max_goals),
    }

def _most_likely_score(matrix, max_goals):
    best, best_p = (0, 0), 0
    for i in range(max_goals):
        for j in range(max_goals):
            if matrix[i][j] > best_p:
                best_p = matrix[i][j]
                best = (i, j)
    return f"{best[0]}-{best[1]}"

def elo_expected(elo_a, elo_b, home_advantage=100):
    elo_a_adj = elo_a + home_advantage
    diff = elo_a_adj - elo_b
    win_prob = 1 / (1 + 10 ** (-diff / 400))
    return {
        "home_win_prob": round(win_prob * 100, 1),
        "away_win_prob": round((1 - win_prob) * 100, 1),
        "elo_home": elo_a,
        "elo_away": elo_b,
        "elo_diff": elo_a - elo_b,
    }

def monte_carlo(lambda_home, lambda_away, n=50000):
    results = {"home_win": 0, "draw": 0, "away_win": 0,
               "over_2_5": 0, "btts": 0, "over_3_5": 0}
    score_counts = {}

    for _ in range(n):
        h = _poisson_sample(lambda_home)
        a = _poisson_sample(lambda_away)
        key = f"{h}-{a}"
        score_counts[key] = score_counts.get(key, 0) + 1
        if h > a: results["home_win"] += 1
        elif h == a: results["draw"] += 1
        else: results["away_win"] += 1
        if h + a > 2: results["over_2_5"] += 1
        if h + a > 3: results["over_3_5"] += 1
        if h > 0 and a > 0: results["btts"] += 1

    top_scores = sorted(score_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "home_win":  round(results["home_win"]  / n * 100, 1),
        "draw":      round(results["draw"]      / n * 100, 1),
        "away_win":  round(results["away_win"]  / n * 100, 1),
        "over_2_5":  round(results["over_2_5"]  / n * 100, 1),
        "over_3_5":  round(results["over_3_5"]  / n * 100, 1),
        "btts":      round(results["btts"]      / n * 100, 1),
        "top_scores": [(s, round(c/n*100, 1)) for s, c in top_scores],
        "simulations": n,
    }

def _poisson_sample(lam):
    L = math.exp(-lam)
    k, p = 0, 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1

def combine_predictions(poisson, monte_carlo_res, elo=None):
    weights = {"poisson": 0.45, "mc": 0.45, "elo": 0.10} if elo else {"poisson": 0.5, "mc": 0.5}
    hw = poisson["home_win"] * weights["poisson"] + monte_carlo_res["home_win"] * weights["mc"]
    dw = poisson["draw"]     * weights["poisson"] + monte_carlo_res["draw"]     * weights["mc"]
    aw = poisson["away_win"] * weights["poisson"] + monte_carlo_res["away_win"] * weights["mc"]
    if elo:
        hw = hw + elo["home_win_prob"] * weights["elo"]
        aw = aw + elo["away_win_prob"] * weights["elo"]
        dw = 100 - hw - aw
    total = hw + dw + aw
    return {
        "home_win": round(hw / total * 100, 1),
        "draw":     round(dw / total * 100, 1),
        "away_win": round(aw / total * 100, 1),
    }

def prob_to_odds(prob_pct):
    if prob_pct <= 0: return 999.0
    return round(100 / prob_pct, 2)
