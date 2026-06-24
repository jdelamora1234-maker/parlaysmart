"""
HOME ADVANTAGE CALCULATOR - Cuantifica ventaja de jugar en casa
Beneficio: Ajusta predicciones por factor cancha
Expectativa: +1-2% ajuste fino
"""

import numpy as np
from typing import Dict, List

class HomeAdvantageCalculator:
    """Calcula y ajusta por ventaja de casa"""

    def calculate_home_advantage(self,
                                team_home_record: Dict,
                                team_away_record: Dict,
                                league: str = "generic") -> Dict:
        """
        Calcula ventaja de jugar en casa

        home_record: {"wins": X, "draws": Y, "losses": Z, "goals_for": A, "goals_against": B}
        """

        # Win rate en casa
        home_wins = team_home_record.get("wins", 0)
        home_total = (team_home_record.get("wins", 0) +
                     team_home_record.get("draws", 0) +
                     team_home_record.get("losses", 0))

        away_wins = team_away_record.get("wins", 0)
        away_total = (team_away_record.get("wins", 0) +
                     team_away_record.get("draws", 0) +
                     team_away_record.get("losses", 0))

        home_win_rate = home_wins / home_total if home_total > 0 else 0.5
        away_win_rate = away_wins / away_total if away_total > 0 else 0.5

        # Ventaja de casa = diferencia entre ambos
        home_advantage = home_win_rate - away_win_rate

        # Goles
        home_goals = team_home_record.get("goals_for", 0) / max(home_total, 1)
        away_goals = team_away_record.get("goals_for", 0) / max(away_total, 1)
        goals_advantage = home_goals - away_goals

        # Liga baseline (varía por liga)
        league_home_advantage = {
            "premier": 0.15,
            "la_liga": 0.14,
            "serie_a": 0.13,
            "bundesliga": 0.14,
            "ligue1": 0.12,
            "generic": 0.14
        }.get(league.lower(), 0.14)

        return {
            "team_home_advantage": round(home_advantage, 3),
            "league_baseline": round(league_home_advantage, 3),
            "adjusted_home_advantage": round(home_advantage * 0.6 + league_home_advantage * 0.4, 3),
            "goals_per_game_home": round(home_goals, 2),
            "goals_per_game_away": round(away_goals, 2),
            "goals_advantage": round(goals_advantage, 2),
            "home_win_rate": round(home_win_rate, 3),
            "away_win_rate": round(away_win_rate, 3),
            "strong_home_team": home_advantage > 0.10
        }

    def adjust_prediction_for_home_advantage(self,
                                            neutral_ground_prediction: float,
                                            home_advantage: float) -> float:
        """
        Ajusta predicción basado en ventaja de casa

        neutral_ground_prediction: probabilidad en cancha neutral
        home_advantage: factor de ajuste
        """

        # Ajuste multiplicativo
        adjusted = neutral_ground_prediction + (home_advantage * 0.3)

        return min(max(adjusted, 0.1), 0.9)  # Bound 10-90%

    def crowd_impact_estimation(self,
                               attendance: int,
                               capacity: int,
                               team_strength: float) -> Dict:
        """
        Estima impacto de la multitud en desempeño
        """

        attendance_pct = attendance / capacity if capacity > 0 else 0.5

        # Mayor asistencia = mayor impacto
        crowd_factor = attendance_pct * 0.10  # Max 10% boost

        # Equipos fuertes se benefician menos
        crowd_factor *= (1 - team_strength * 0.3)

        return {
            "attendance_pct": round(attendance_pct * 100, 1),
            "crowd_advantage_pct": round(crowd_factor * 100, 1),
            "crowd_impact": (
                "MAJOR" if crowd_factor > 0.07 else
                "SIGNIFICANT" if crowd_factor > 0.04 else
                "MODERATE"
            ),
            "expectation": "FAVOR_HOME_TEAM"
        }

    def historical_home_advantage_by_stadium(self,
                                             stadium: str,
                                             historical_results: List[Dict]) -> Dict:
        """
        Calcula ventaja histórica específica de cada estadio

        Algunos estadios son más favorables que otros
        """

        home_wins = sum(1 for r in historical_results if r.get("home_won"))
        home_total = len(historical_results)

        home_win_rate = home_wins / home_total if home_total > 0 else 0.5

        # Ajuste: qué tan por encima/debajo de 55% (base home advantage)
        stadium_advantage = (home_win_rate - 0.55) * 2  # 2x multiplier

        return {
            "stadium": stadium,
            "home_win_rate": round(home_win_rate, 3),
            "stadium_specific_advantage": round(stadium_advantage, 3),
            "sample_size": home_total,
            "strength": (
                "VERY_STRONG" if stadium_advantage > 0.20 else
                "STRONG" if stadium_advantage > 0.10 else
                "AVERAGE"
            ),
            "confidence": "LOW" if home_total < 10 else "MEDIUM" if home_total < 20 else "HIGH"
        }


home_calculator = HomeAdvantageCalculator()

if __name__ == "__main__":
    print("[TEST] Home Advantage Calculator\n")
    home_record = {"wins": 10, "draws": 3, "losses": 2, "goals_for": 35, "goals_against": 12}
    away_record = {"wins": 6, "draws": 2, "losses": 7, "goals_for": 22, "goals_against": 28}

    result = home_calculator.calculate_home_advantage(home_record, away_record, "premier")
    print(f"Home advantage: {result['adjusted_home_advantage']}")
    print(f"Strong home team: {result['strong_home_team']}")
