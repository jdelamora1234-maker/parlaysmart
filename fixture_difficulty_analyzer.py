"""
FIXTURE DIFFICULTY ANALYZER - Analiza dificultad de próximas jornadas
Beneficio: Detectar equipos con calendarios fáciles/difíciles
Expectativa: +2-3% mejor fixture timing
"""

import numpy as np
from typing import Dict, List

class FixtureDifficultyAnalyzer:
    """Analiza dificultad de calendarios"""

    def __init__(self):
        self.team_ratings = {}  # ELO or similar

    def calculate_fixture_difficulty(self,
                                     upcoming_opponents: List[str],
                                     opponent_strengths: List[float]) -> Dict:
        """
        Calcula dificultad de próximas jornadas

        opponent_strengths: ratings ELO/strength (0-1)
        """

        if not upcoming_opponents:
            return {"error": "No fixtures"}

        avg_difficulty = np.mean(opponent_strengths)
        max_difficulty = max(opponent_strengths)
        min_difficulty = min(opponent_strengths)

        # Contar rivales top 6
        top_teams = sum(1 for s in opponent_strengths if s > 0.7)

        # Expected points (assuming 50% baseline)
        expected_points = sum((1 - s) * 3 for s in opponent_strengths)  # 3 points per win

        return {
            "num_fixtures": len(upcoming_opponents),
            "average_difficulty": round(avg_difficulty, 3),
            "max_difficulty": round(max_difficulty, 3),
            "min_difficulty": round(min_difficulty, 3),
            "top_6_opponents": top_teams,
            "expected_points": round(expected_points, 1),
            "expected_wins": round(expected_points / 3, 1),
            "difficulty_rating": (
                "VERY_HARD" if avg_difficulty > 0.75 else
                "HARD" if avg_difficulty > 0.60 else
                "MODERATE" if avg_difficulty > 0.45 else
                "EASY" if avg_difficulty > 0.30 else
                "VERY_EASY"
            ),
            "recommendation": (
                "AVOID_BETTING" if avg_difficulty > 0.75 else
                "SELECTIVE_BETTING" if avg_difficulty > 0.60 else
                "AGGRESSIVE_BETTING"
            ),
        }

    def compare_fixture_schedules(self,
                                 team_a_fixtures: List[float],
                                 team_b_fixtures: List[float]) -> Dict:
        """
        Compara dificultad de calendarios entre dos equipos
        """

        avg_a = np.mean(team_a_fixtures)
        avg_b = np.mean(team_b_fixtures)

        advantage = avg_b - avg_a  # Positive = team_a has easier fixtures

        return {
            "team_a_avg_difficulty": round(avg_a, 3),
            "team_b_avg_difficulty": round(avg_b, 3),
            "advantage": "TEAM_A" if advantage > 0.05 else "TEAM_B" if advantage < -0.05 else "EQUAL",
            "advantage_pct": round(abs(advantage) * 100, 1),
            "implication": "TEAM_A_FAVORED" if advantage > 0.1 else "TEAM_B_FAVORED" if advantage < -0.1 else "NEUTRAL",
        }

    def identify_momentum_windows(self,
                                 fixtures: List[Dict]) -> Dict:
        """
        Identifica ventanas donde el equipo puede coger momentum

        Momentum window = secuencia de rivales débiles
        """

        momentum_windows = []
        current_window = []
        window_strength = []

        for fixture in fixtures:
            difficulty = fixture.get("difficulty", 0.5)

            if difficulty < 0.5:  # Easy match
                current_window.append(fixture.get("opponent", "?"))
                window_strength.append(difficulty)
            else:  # Difficult match
                if current_window:
                    momentum_windows.append({
                        "window": current_window,
                        "avg_difficulty": round(np.mean(window_strength), 3),
                        "matches": len(current_window),
                    })
                current_window = []
                window_strength = []

        # Last window
        if current_window:
            momentum_windows.append({
                "window": current_window,
                "avg_difficulty": round(np.mean(window_strength), 3),
                "matches": len(current_window),
            })

        return {
            "momentum_windows_found": len(momentum_windows),
            "windows": momentum_windows,
            "best_window": max(momentum_windows, key=lambda x: x["matches"]) if momentum_windows else None,
            "recommendation": "ACCUMULATE_DURING_EASY_RUN" if momentum_windows else "NO_EASY_RUNS",
        }


fixture_analyzer = FixtureDifficultyAnalyzer()


if __name__ == "__main__":
    print("[TEST] Fixture Difficulty Analyzer\n")

    opponents = ["Team A", "Team B", "Team C"]
    strengths = [0.65, 0.75, 0.55]

    result = fixture_analyzer.calculate_fixture_difficulty(opponents, strengths)
    print(f"Avg difficulty: {result['average_difficulty']}")
    print(f"Rating: {result['difficulty_rating']}")
