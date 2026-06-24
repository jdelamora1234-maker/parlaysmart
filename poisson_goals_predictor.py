"""
POISSON GOALS PREDICTOR - Predicción exacta de goles
Usa: Poisson distribution + team strength + head-to-head
Beneficio: Predecir Over/Under, correct score, both teams score
"""

import math
from scipy.stats import poisson
from typing import Dict, Tuple, List

class PoissonGoalsPredictor:
    """Predice distribución de goles usando Poisson"""

    def __init__(self):
        self.team_stats = {}
        self.head_to_head = {}

    def calculate_lambda(self,
                        team_attack_rating: float,
                        opponent_defense_rating: float,
                        home_advantage: float = 1.2) -> float:
        """
        Calcula lambda (expected goals) para Poisson

        λ = attack_rating × defense_rating × home_advantage

        attack_rating: qué tan ofensivo es el equipo
        defense_rating: qué tan defensivo es el oponente
        home_advantage: ventaja de jugar en casa (~1.2x)
        """

        # Normalizar: ambas ratings entre 0.5 y 2.0
        attack = max(0.5, min(2.0, team_attack_rating))
        defense = max(0.5, min(2.0, opponent_defense_rating))

        lambda_xg = attack * defense * home_advantage

        return round(lambda_xg, 2)

    def predict_exact_score(self,
                           lambda_home: float,
                           lambda_away: float,
                           max_goals: int = 5) -> Dict[Tuple[int, int], float]:
        """
        Predice probabilidad de cada score exacto

        Ejemplo: {(2, 1): 0.12, (1, 1): 0.18, ...}
        """

        probabilities = {}

        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                # P(home_goals) × P(away_goals)
                p_home = poisson.pmf(home_goals, lambda_home)
                p_away = poisson.pmf(away_goals, lambda_away)
                p_score = p_home * p_away

                if p_score > 0.001:  # Solo scores con > 0.1% probabilidad
                    probabilities[(home_goals, away_goals)] = round(p_score, 4)

        return probabilities

    def predict_match_outcomes(self,
                              lambda_home: float,
                              lambda_away: float) -> Dict[str, float]:
        """
        Predice resultados: Home Win, Draw, Away Win
        """

        # Calcular probabilidades de goles acumuladas
        p_home_win = 0
        p_draw = 0
        p_away_win = 0

        for home_goals in range(10):
            for away_goals in range(10):
                p_score = poisson.pmf(home_goals, lambda_home) * poisson.pmf(away_goals, lambda_away)

                if home_goals > away_goals:
                    p_home_win += p_score
                elif home_goals == away_goals:
                    p_draw += p_score
                else:
                    p_away_win += p_score

        return {
            "home_win": round(p_home_win, 3),
            "draw": round(p_draw, 3),
            "away_win": round(p_away_win, 3),
        }

    def predict_over_under(self,
                          lambda_home: float,
                          lambda_away: float,
                          threshold: float = 2.5) -> Dict[str, float]:
        """
        Predice Over/Under de goles totales

        Over 2.5: more than 2 goals
        Under 2.5: 2 or fewer goals
        """

        p_over = 0
        p_under = 0

        for total_goals in range(10):
            for home_goals in range(total_goals + 1):
                away_goals = total_goals - home_goals

                p_score = poisson.pmf(home_goals, lambda_home) * poisson.pmf(away_goals, lambda_away)

                if total_goals > threshold:
                    p_over += p_score
                else:
                    p_under += p_score

        return {
            "over": round(p_over, 3),
            "under": round(p_under, 3),
            "threshold": threshold,
        }

    def predict_both_teams_score(self,
                                lambda_home: float,
                                lambda_away: float) -> Dict[str, float]:
        """
        Predice: Both Teams Score (BTTS)?
        """

        p_btts = 0

        for home_goals in range(1, 10):  # Home >= 1
            for away_goals in range(1, 10):  # Away >= 1
                p_score = poisson.pmf(home_goals, lambda_home) * poisson.pmf(away_goals, lambda_away)
                p_btts += p_score

        return {
            "btts_yes": round(p_btts, 3),
            "btts_no": round(1 - p_btts, 3),
        }

    def predict_correct_score_market(self,
                                    lambda_home: float,
                                    lambda_away: float) -> List[Tuple[str, float]]:
        """
        Predice scores populares en el mercado

        Retorna: [("0-0", 0.05), ("1-0", 0.12), ...]
        """

        exact_scores = self.predict_exact_score(lambda_home, lambda_away)

        popular_scores = [
            (0, 0), (1, 0), (2, 0), (3, 0),
            (0, 1), (1, 1), (2, 1), (3, 1),
            (0, 2), (1, 2), (2, 2),
            (0, 3), (1, 3),
        ]

        market_scores = []
        for score in popular_scores:
            prob = exact_scores.get(score, 0)
            if prob > 0.001:
                market_scores.append((f"{score[0]}-{score[1]}", prob))

        # Otros scores agrupados
        other_prob = sum(p for s, p in exact_scores.items() if s not in popular_scores)
        if other_prob > 0.001:
            market_scores.append(("3+", other_prob))

        return sorted(market_scores, key=lambda x: x[1], reverse=True)

    def compare_with_market(self,
                           lambda_home: float,
                           lambda_away: float,
                           market_odds: Dict[str, float]) -> Dict[str, Dict]:
        """
        Compara predicciones Poisson vs odds del mercado

        Encuentra discrepancias
        """

        predictions = self.predict_match_outcomes(lambda_home, lambda_away)
        comparisons = {}

        for outcome, our_prob in predictions.items():
            # Convertir outcome a odds key
            if outcome == "home_win":
                odds_key = "home"
            elif outcome == "away_win":
                odds_key = "away"
            else:
                odds_key = "draw"

            market_odds_val = market_odds.get(odds_key, 2.0)
            market_prob = 1 / market_odds_val if market_odds_val > 0 else 0.5

            # Calcular edge
            our_fair_odds = 1 / our_prob if our_prob > 0 else 2.0
            edge = (our_fair_odds - market_odds_val) / market_odds_val

            comparisons[outcome] = {
                "our_probability": round(our_prob, 3),
                "our_fair_odds": round(our_fair_odds, 2),
                "market_odds": round(market_odds_val, 2),
                "market_probability": round(market_prob, 3),
                "edge_pct": round(edge * 100, 2),
                "value": "YES" if edge > 0.05 else "NO",
            }

        return comparisons

    def estimate_team_stats(self,
                           recent_matches: List[Dict]) -> Tuple[float, float]:
        """
        Estima attack y defense ratings de últimos partidos

        Desde histórico de resultados
        """

        total_gf = sum(m.get("goals_for", 0) for m in recent_matches)
        total_ga = sum(m.get("goals_against", 0) for m in recent_matches)
        matches_count = len(recent_matches)

        if matches_count == 0:
            return 1.0, 1.0

        avg_gf = total_gf / matches_count
        avg_ga = total_ga / matches_count

        # Rating: qué tan arriba o abajo del promedio (1.5 en la liga)
        attack_rating = avg_gf / 1.5
        defense_rating = 1.5 / (avg_ga + 0.1)  # +0.1 para evitar división por cero

        return round(attack_rating, 2), round(defense_rating, 2)


# Singleton
predictor = PoissonGoalsPredictor()


if __name__ == "__main__":
    print("[TEST] Poisson Goals Predictor\n")

    # Test predict exact score
    lambda_home = 1.8
    lambda_away = 0.9

    print(f"λ_home = {lambda_home}, λ_away = {lambda_away}\n")

    # 1. Outcomes
    outcomes = predictor.predict_match_outcomes(lambda_home, lambda_away)
    print("Match Outcomes:")
    for outcome, prob in outcomes.items():
        print(f"  {outcome}: {prob*100:.1f}%")

    # 2. Over/Under
    ou = predictor.predict_over_under(lambda_home, lambda_away)
    print(f"\nOver/Under 2.5:")
    print(f"  Over: {ou['over']*100:.1f}%")
    print(f"  Under: {ou['under']*100:.1f}%")

    # 3. BTTS
    btts = predictor.predict_both_teams_score(lambda_home, lambda_away)
    print(f"\nBoth Teams Score:")
    print(f"  Yes: {btts['btts_yes']*100:.1f}%")
    print(f"  No: {btts['btts_no']*100:.1f}%")

    # 4. Correct Score
    scores = predictor.predict_correct_score_market(lambda_home, lambda_away)
    print(f"\nTop Correct Scores:")
    for score, prob in scores[:5]:
        print(f"  {score}: {prob*100:.2f}%")

    # 5. Compare with market
    market_odds = {"home": 2.0, "draw": 3.2, "away": 3.5}
    comp = predictor.compare_with_market(lambda_home, lambda_away, market_odds)
    print(f"\nComparison with Market:")
    import json
    print(json.dumps(comp, indent=2))
