"""
HISTORICAL PATTERN MATCHER - Encuentra partidos similares en la historia
Beneficio: "Si pasó algo similar antes, probablemente pase algo similar ahora"
Expectativa: +3-5% por coincidencias históricas
"""

import numpy as np
from typing import Dict, List, Tuple

class HistoricalPatternMatcher:
    """Encuentra y aprende de patrones históricos"""

    def __init__(self):
        self.historical_matches = []

    def calculate_match_similarity(self,
                                  current_match: Dict,
                                  historical_match: Dict) -> float:
        """
        Calcula similitud entre dos partidos

        Factores: equipos, forma, jugadores clave, etc.
        """

        similarity = 0
        max_similarity = 0

        # Comparar equipos
        if current_match.get("home_team") == historical_match.get("home_team"):
            similarity += 0.2
        if current_match.get("away_team") == historical_match.get("away_team"):
            similarity += 0.2
        max_similarity += 0.4

        # Comparar forma
        home_form_sim = 1 - abs(
            current_match.get("home_form", 0.5) -
            historical_match.get("home_form", 0.5)
        ) * 0.5
        away_form_sim = 1 - abs(
            current_match.get("away_form", 0.5) -
            historical_match.get("away_form", 0.5)
        ) * 0.5

        similarity += (home_form_sim + away_form_sim) * 0.1
        max_similarity += 0.2

        # Comparar clave players
        home_key_same = len(set(current_match.get("home_key_players", [])) &
                           set(historical_match.get("home_key_players", [])))
        away_key_same = len(set(current_match.get("away_key_players", [])) &
                           set(historical_match.get("away_key_players", [])))

        similarity += (home_key_same + away_key_same) * 0.05
        max_similarity += 0.1

        # Contexto (liga, temporada, etc.)
        if current_match.get("league") == historical_match.get("league"):
            similarity += 0.15
        max_similarity += 0.15

        # Normalizar
        normalized = similarity / max_similarity if max_similarity > 0 else 0

        return min(normalized, 1.0)

    def find_similar_historical_matches(self,
                                       current_match: Dict,
                                       num_matches: int = 5) -> List[Dict]:
        """
        Encuentra los N partidos más similares en la historia
        """

        if not self.historical_matches:
            return []

        similarities = []

        for hist_match in self.historical_matches:
            sim = self.calculate_match_similarity(current_match, hist_match)
            similarities.append({
                "match": hist_match,
                "similarity_score": sim
            })

        # Ordenar por similitud
        similarities.sort(key=lambda x: x["similarity_score"], reverse=True)

        return similarities[:num_matches]

    def extract_pattern_from_similar_matches(self,
                                            similar_matches: List[Dict]) -> Dict:
        """
        Extrae patrón común de partidos similares

        Si la mayoría resultó en HOME_WIN, entonces HOME_WIN es probable
        """

        if not similar_matches:
            return {"error": "No similar matches"}

        outcomes = [m.get("match", {}).get("result", "DRAW") for m in similar_matches]

        # Contar resultados
        home_wins = outcomes.count("HOME_WIN")
        draws = outcomes.count("DRAW")
        away_wins = outcomes.count("AWAY_WIN")

        total = len(outcomes)

        return {
            "total_similar_matches": total,
            "home_win_frequency": round(home_wins / total, 3),
            "draw_frequency": round(draws / total, 3),
            "away_win_frequency": round(away_wins / total, 3),
            "most_likely_outcome": max(
                ("HOME_WIN", home_wins),
                ("DRAW", draws),
                ("AWAY_WIN", away_wins),
                key=lambda x: x[1]
            )[0],
            "pattern_strength": round(max(home_wins, draws, away_wins) / total, 3),
            "confidence": (
                "HIGH" if max(home_wins, draws, away_wins) / total > 0.65 else
                "MODERATE" if max(home_wins, draws, away_wins) / total > 0.50 else
                "LOW"
            ),
        }

    def predict_using_historical_pattern(self,
                                        pattern: Dict,
                                        pre_match_prediction: float) -> Dict:
        """
        Ajusta predicción usando patrón histórico

        Combina predicción previa con patrón histórico
        """

        pattern_confidence = {
            "HOME_WIN": pattern.get("home_win_frequency", 0.33),
            "DRAW": pattern.get("draw_frequency", 0.33),
            "AWAY_WIN": pattern.get("away_win_frequency", 0.33),
        }

        # Ponderación: 60% predicción previa, 40% histórico
        combined = (pre_match_prediction * 0.6) + (pattern_confidence.get("HOME_WIN", 0.33) * 0.4)

        return {
            "pre_match_prediction": round(pre_match_prediction, 3),
            "historical_pattern_prediction": round(pattern_confidence.get("HOME_WIN", 0.33), 3),
            "combined_prediction": round(combined, 3),
            "pattern_strength": pattern.get("pattern_strength", 0),
            "final_recommendation": (
                "FOLLOW_PATTERN" if pattern.get("pattern_strength", 0) > 0.65 else
                "BLEND_WITH_MODEL" if pattern.get("pattern_strength", 0) > 0.50 else
                "RELY_ON_MODEL"
            ),
        }


pattern_matcher = HistoricalPatternMatcher()

if __name__ == "__main__":
    print("[TEST] Historical Pattern Matcher\n")
    print("Pattern matching engine ready")
