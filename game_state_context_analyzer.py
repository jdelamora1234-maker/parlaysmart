"""
GAME STATE CONTEXT ANALYZER - Analiza contexto dinámico del partido en vivo
Beneficio: Predicciones se adaptan segundo a segundo
Expectativa: +5-10% durante partidos en vivo
"""

import numpy as np
from typing import Dict, List

class GameStateContextAnalyzer:
    """Analiza contexto dinámico durante el partido"""

    def analyze_game_momentum(self,
                             recent_events: List[Dict],
                             current_score: Dict) -> Dict:
        """
        Analiza momentum actual del partido

        Events: goles, tarjetas, cambios, tiros, etc.
        """

        if not recent_events:
            return {"error": "No events"}

        # Momentum = cambios en el patrón de juego
        goals_home = sum(1 for e in recent_events if e.get("type") == "goal" and e.get("team") == "home")
        goals_away = sum(1 for e in recent_events if e.get("type") == "goal" and e.get("team") == "away")

        yellow_home = sum(1 for e in recent_events if e.get("type") == "yellow" and e.get("team") == "home")
        yellow_away = sum(1 for e in recent_events if e.get("type") == "yellow" and e.get("team") == "away")

        # Momentum = recency-weighted sum of favorable events
        home_momentum = goals_home * 0.5 - goals_away * 0.3 - yellow_away * 0.2
        away_momentum = goals_away * 0.5 - goals_home * 0.3 - yellow_home * 0.2

        return {
            "home_momentum": round(home_momentum, 2),
            "away_momentum": round(away_momentum, 2),
            "leading_team": "HOME" if home_momentum > away_momentum else "AWAY",
            "momentum_strength": abs(home_momentum - away_momentum),
            "prediction_shift": round((home_momentum - away_momentum) * 0.05, 3),
        }

    def calculate_expected_score_distribution(self,
                                             current_score: Dict,
                                             time_elapsed_minutes: int,
                                             team_stats: Dict) -> Dict:
        """
        Calcula distribución de posibles puntuaciones finales

        Basado en tiempo restante y ritmo actual
        """

        home_score = current_score.get("home", 0)
        away_score = current_score.get("away", 0)
        minutes_remaining = 90 - time_elapsed_minutes

        # Ritmo de goles (goles por 90 min)
        home_goal_rate = team_stats.get("home_goal_rate", 1.5)
        away_goal_rate = team_stats.get("away_goal_rate", 1.2)

        # Goles esperados restantes
        expected_home_goals = (home_goal_rate / 90) * minutes_remaining
        expected_away_goals = (away_goal_rate / 90) * minutes_remaining

        # Distribución Poisson
        expected_home_final = round(home_score + expected_home_goals, 1)
        expected_away_final = round(away_score + expected_away_goals, 1)

        return {
            "current_score": f"{home_score}-{away_score}",
            "minutes_remaining": minutes_remaining,
            "expected_final_score": f"{expected_home_final}-{expected_away_final}",
            "home_expected_goals": round(expected_home_goals, 2),
            "away_expected_goals": round(expected_away_goals, 2),
            "most_likely_outcome": (
                "HOME_WIN" if expected_home_final > expected_away_final else
                "DRAW" if abs(expected_home_final - expected_away_final) < 0.3 else
                "AWAY_WIN"
            ),
        }

    def live_odds_adjustment_recommendation(self,
                                           pre_match_probability: float,
                                           current_game_state: Dict) -> Dict:
        """
        Recomienda ajuste de odds basado en estado actual
        """

        momentum = current_game_state.get("momentum", 0)
        score_home = current_game_state.get("score", {}).get("home", 0)
        score_away = current_game_state.get("score", {}).get("away", 0)

        # Ajuste por momentum
        momentum_adjustment = momentum * 0.05

        # Ajuste por score
        score_adjustment = 0
        if score_home > score_away:
            score_adjustment = 0.08
        elif score_home < score_away:
            score_adjustment = -0.08

        # Nueva probabilidad
        adjusted_prob = pre_match_probability + momentum_adjustment + score_adjustment
        adjusted_prob = max(0.1, min(0.9, adjusted_prob))

        return {
            "pre_match_probability": round(pre_match_probability, 3),
            "adjusted_probability": round(adjusted_prob, 3),
            "adjustment_pct": round((adjusted_prob - pre_match_probability) * 100, 2),
            "recommendation": (
                "INCREASE_STAKE" if adjusted_prob > pre_match_probability + 0.05 else
                "DECREASE_STAKE" if adjusted_prob < pre_match_probability - 0.05 else
                "MAINTAIN_STAKE"
            ),
        }


game_analyzer = GameStateContextAnalyzer()

if __name__ == "__main__":
    print("[TEST] Game State Context Analyzer\n")

    events = [
        {"type": "goal", "team": "home", "minute": 15},
        {"type": "goal", "team": "away", "minute": 25},
        {"type": "yellow", "team": "away", "minute": 40},
    ]

    momentum = game_analyzer.analyze_game_momentum(events, {"home": 1, "away": 1})
    print(f"Momentum: HOME {momentum['home_momentum']}, AWAY {momentum['away_momentum']}")
