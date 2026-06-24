"""
VALUE BETTING DETECTOR - Encuentra oportunidades de valor
Compara: Fair Odds (nuestro análisis) vs Market Odds (casas)
Si fair > market = VALUE BET (explotar)
Beneficio: +5-10% ROI adicional
"""

import numpy as np
from typing import Dict, List, Tuple

class ValueDetector:
    """Detecta value bets comparando análisis vs mercado"""

    def __init__(self, min_value_threshold: float = 0.10):
        """
        min_value_threshold: Mínimo valor (10% = apuesta que debe estar +10% arriba del fair)
        """
        self.min_value_threshold = min_value_threshold

    def calculate_fair_odds(self, probability: float) -> float:
        """
        Calcula fair odds desde probabilidad
        Fair Odds = 1 / probability
        """
        if probability <= 0 or probability >= 1:
            return 0

        return round(1 / probability, 3)

    def detect_value_bet(self,
                        our_probability: float,
                        market_odds: float,
                        threshold: float = None) -> Dict[str, any]:
        """
        Detecta si hay value bet

        our_probability: Nuestra predicción (0-1)
        market_odds: Odds de la casa
        """

        if threshold is None:
            threshold = self.min_value_threshold

        # Fair odds según nuestro análisis
        fair_odds = self.calculate_fair_odds(our_probability)

        # Market probability implícita
        market_probability = 1 / market_odds if market_odds > 0 else 0

        # Value = (fair_odds - market_odds) / market_odds
        if market_odds > 0:
            value = (fair_odds - market_odds) / market_odds
        else:
            value = 0

        # Es value bet si:
        # 1. Fair odds > Market odds
        # 2. Value >= threshold
        is_value_bet = (fair_odds > market_odds) and (value >= threshold)

        return {
            "our_probability": round(our_probability, 3),
            "our_fair_odds": fair_odds,
            "market_odds": market_odds,
            "market_probability": round(market_probability, 3),
            "value": round(value, 4),
            "value_pct": round(value * 100, 2),
            "is_value_bet": is_value_bet,
            "confidence": round(fair_odds / market_odds, 2) if market_odds > 0 else 0,
        }

    def find_best_value_bets(self,
                            predictions: Dict[str, Tuple[float, float]],
                            threshold: float = None) -> List[Dict]:
        """
        Encuentra los mejores value bets en una lista

        predictions: {
            "parlay_name": (our_prob, market_odds),
            ...
        }
        """

        value_bets = []

        for parlay_name, (prob, odds) in predictions.items():
            detection = self.detect_value_bet(prob, odds, threshold)

            if detection["is_value_bet"]:
                detection["parlay_name"] = parlay_name
                value_bets.append(detection)

        # Ordenar por value descendente
        value_bets.sort(key=lambda x: x["value"], reverse=True)

        return value_bets

    def detect_arbitrage(self,
                        outcome_odds: Dict[str, float],
                        threshold: float = 0.02) -> bool:
        """
        Detecta arbitrage (oportunidad garantizada de ganancia)

        outcome_odds: {
            "home": 1.95,
            "draw": 3.20,
            "away": 3.50
        }

        Existe arbitrage si sum(1/odds) < 1
        """

        inverse_sum = sum(1/odds for odds in outcome_odds.values() if odds > 0)

        # Margen de arbitrage
        arbitrage_margin = 1 - inverse_sum

        return {
            "has_arbitrage": arbitrage_margin > threshold,
            "margin": round(arbitrage_margin * 100, 2),
            "guaranteed_roi": round((1 / (1 - arbitrage_margin) - 1) * 100, 2) if arbitrage_margin < 1 else 0,
        }

    def rank_parlays_by_value(self,
                              parlays: Dict[str, Dict]) -> List[Tuple[str, float]]:
        """
        Rankea parlays por valor (highest first)

        parlays: {
            "ultra": {"prob": 0.78, "odds": 1.75, "ev": 0.22},
            ...
        }
        """

        ranked = []

        for parlay_name, data in parlays.items():
            prob = data.get("prob", 0.5)
            odds = data.get("odds", 1.5)
            ev = data.get("ev", 0)

            # Value = (fair_odds - market_odds) / market_odds
            fair_odds = self.calculate_fair_odds(prob)
            value = (fair_odds - odds) / odds if odds > 0 else 0

            ranked.append((parlay_name, round(value, 4)))

        # Ordenar descendente
        ranked.sort(key=lambda x: x[1], reverse=True)

        return ranked


# Singleton
value = ValueDetector()


if __name__ == "__main__":
    print("[TEST] Value Betting Detector\n")

    # Test 1: Detect value bet
    print("TEST 1: Single value bet detection")
    detection = value.detect_value_bet(0.62, 3.2)  # 62% prob, market 3.2
    print(f"Our prob: 62%, Market odds: 3.2")
    print(f"  Fair odds: {detection['our_fair_odds']}")
    print(f"  Value: {detection['value_pct']}%")
    print(f"  Is value bet: {detection['is_value_bet']}\n")

    # Test 2: Find best value bets
    print("TEST 2: Find best value bets")
    predictions = {
        "ultra": (0.78, 1.75),  # 78% prob, 1.75 odds
        "conservador": (0.62, 3.2),  # 62% prob, 3.2 odds
        "balanceado": (0.41, 6.8),  # 41% prob, 6.8 odds
        "riesgoso": (0.22, 18.5),  # 22% prob, 18.5 odds
    }

    value_bets = value.find_best_value_bets(predictions)
    print(f"Found {len(value_bets)} value bets:")
    for bet in value_bets:
        print(f"  {bet['parlay_name']}: {bet['value_pct']}% value")

    print()

    # Test 3: Arbitrage
    print("TEST 3: Arbitrage detection")
    outcome_odds = {
        "home": 1.95,
        "draw": 3.20,
        "away": 3.50
    }
    arb = value.detect_arbitrage(outcome_odds)
    print(f"Home: 1.95, Draw: 3.20, Away: 3.50")
    print(f"  Has arbitrage: {arb['has_arbitrage']}")
    print(f"  Margin: {arb['margin']}%")
