"""
RED CARD PROBABILITY PREDICTOR - Predice probabilidad de tarjetas rojas
Beneficio: Impacta ENORMEMENTE el resultado (11 vs 10)
Expectativa: +3-5% por predicción de tarjetas
"""

import numpy as np
from typing import Dict, List

class RedCardPredictor:
    """Predice probabilidad de tarjetas rojas"""

    def __init__(self):
        self.player_card_history = {}

    def estimate_player_red_card_risk(self, player: Dict) -> Dict:
        """
        Estima riesgo de tarjeta roja para un jugador

        Factores:
        - Historial de tarjetas
        - Estilo de juego
        - Rival (equipo defensivo vs ataque)
        - Árbitro (estricto vs permisivo)
        """

        yellows = player.get("yellow_cards", 0)
        reds = player.get("red_cards", 0)
        fouls_per_game = player.get("fouls_per_game", 2.0)
        position = player.get("position", "MID")

        # Base risk por historial
        red_card_base_risk = 0.02  # 2% base

        # Aumentar por tarjetas amarillas acumuladas
        if yellows >= 8:
            red_card_base_risk += 0.05  # Riesgo de acumulación
        elif yellows >= 5:
            red_card_base_risk += 0.02

        # Aumentar por historial de rojas
        red_card_base_risk += reds * 0.01

        # Aumentar por agresividad (fouls)
        red_card_base_risk += (fouls_per_game - 1.5) * 0.01

        # Aumentar por posición (defensores más riesgo)
        if position == "DEF":
            red_card_base_risk *= 1.3
        elif position == "FWD":
            red_card_base_risk *= 0.8

        # Capear riesgo máximo
        risk = min(red_card_base_risk, 0.15)

        return {
            "player": player.get("name", "Unknown"),
            "red_card_probability": round(risk, 3),
            "risk_level": (
                "VERY_HIGH" if risk > 0.12 else
                "HIGH" if risk > 0.08 else
                "MODERATE" if risk > 0.04 else
                "LOW"
            ),
            "recommendation": "CONSIDER_BENCHING" if risk > 0.10 else "MONITOR_CLOSELY" if risk > 0.06 else "OK"
        }

    def team_red_card_impact(self, team: Dict, opposing_team_style: str = "neutral") -> Dict:
        """
        Impacto estimado de tarjeta roja en el equipo

        Si jugador clave se va rojo = enorme impacto
        """

        key_players = [p for p in team.get("squad", []) if p.get("importance", 0) > 0.7]

        risk_sum = 0
        weighted_risk = 0

        for player in key_players:
            risk = self.estimate_player_red_card_risk(player).get("red_card_probability", 0)
            importance = player.get("importance", 0.5)

            risk_sum += risk
            weighted_risk += risk * importance

        # Probabilidad de al menos una tarjeta roja en un equipo
        # P(at least 1) = 1 - P(no reds) = 1 - ∏(1-p_i)
        prob_no_reds = np.prod([1 - p.get("red_card_probability", 0)
                               for p in key_players])
        prob_at_least_one = 1 - prob_no_reds

        # Impacto en probabilidad de ganar
        if opposing_team_style == "aggressive":
            prob_at_least_one *= 1.2

        impact_on_win_prob = (
            weighted_risk * 0.15 if weighted_risk > 0.05 else 0
        )

        return {
            "key_players_at_risk": len(key_players),
            "probability_of_red_card": round(prob_at_least_one, 3),
            "expected_impact_on_win_prob": round(-impact_on_win_prob, 3),
            "severity": (
                "CRITICAL" if prob_at_least_one > 0.15 else
                "HIGH" if prob_at_least_one > 0.10 else
                "MODERATE"
            ),
            "recommendation": "REDUCE_ODDS" if prob_at_least_one > 0.10 else "MONITOR"
        }

    def referee_strictness_adjustment(self, referee: Dict) -> float:
        """
        Ajusta riesgo de roja basado en árbitro

        Árbitros estrictos = más rojas
        """

        red_cards_given = referee.get("red_cards_per_season", 5)
        yellow_cards_given = referee.get("yellow_cards_per_season", 80)

        strictness = (red_cards_given / 50) * 0.5 + (yellow_cards_given / 150) * 0.5

        return min(strictness, 2.0)  # Cap at 2x multiplier


red_card_predictor = RedCardPredictor()

if __name__ == "__main__":
    print("[TEST] Red Card Predictor\n")
    player = {
        "name": "Aggressive Player",
        "yellow_cards": 6,
        "red_cards": 1,
        "fouls_per_game": 2.8,
        "position": "DEF"
    }
    result = red_card_predictor.estimate_player_red_card_risk(player)
    print(f"Red card risk: {result['red_card_probability']}")
    print(f"Level: {result['risk_level']}")
