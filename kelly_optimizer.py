"""
KELLY CRITERION OPTIMIZER - Maximizar EV con Kelly Criterion
Fórmula: f* = (bp - q) / b
Beneficio: Optimizar stake para máxima ganancia a largo plazo
Implementación: Kelly × fraction (50%, 75%, 100%) según confianza
"""

import numpy as np
from typing import Dict, Tuple

class KellyCriterionOptimizer:
    """Calcula optimal stake usando Kelly Criterion"""

    def __init__(self):
        self.min_probability = 0.01  # Evitar division por cero
        self.max_kelly = 0.25  # Máximo 25% del bankroll

    def calculate_kelly(self, win_prob: float, odds: float) -> float:
        """
        Calcula Kelly Criterion

        f* = (bp - q) / b
        donde:
        - b = decimal odds - 1 (e.g., 2.0 → 1.0)
        - p = win probability
        - q = 1 - p (loss probability)

        Resultado: Fracción del bankroll a apostar
        """

        if win_prob < self.min_probability or win_prob > 0.99:
            return 0

        # Convertir a decimal si es necesario
        if odds < 1.01:
            return 0

        # Calcular parámetros
        b = odds - 1  # Payoff
        p = win_prob
        q = 1 - p

        # Kelly formula
        kelly = (b * p - q) / b

        # Asegurar que sea positivo y dentro de límites
        kelly = max(0, min(kelly, self.max_kelly))

        return round(kelly, 4)

    def calculate_kelly_with_confidence(self,
                                       win_prob: float,
                                       odds: float,
                                       confidence: float = 0.5) -> Dict[str, float]:
        """
        Calcula Kelly con fracción según confianza

        confidence: 0.0 - 1.0 (qué tan seguro estamos)
        """

        kelly_full = self.calculate_kelly(win_prob, odds)

        # Fracciones según confianza
        if confidence > 0.75:
            fraction = 1.0  # Full Kelly
        elif confidence > 0.60:
            fraction = 0.75  # 75% Kelly
        else:
            fraction = 0.50  # 50% Kelly (conservative)

        kelly_fraction = kelly_full * fraction

        return {
            "kelly_full": kelly_full,
            "kelly_fraction": kelly_fraction,
            "confidence": confidence,
            "stake_fraction": fraction,
        }

    def optimize_parlay_allocation(self,
                                   parlays: Dict[str, Dict],
                                   bankroll: float = 1000) -> Dict[str, Dict]:
        """
        Asigna stake óptimo a cada parlay usando Kelly

        parlays: {
            "ultra": {"prob": 0.78, "odds": 1.75, "confidence": 0.9},
            ...
        }
        """

        optimized = {}
        total_allocation = 0

        for parlay_type, data in parlays.items():
            prob = data.get("prob", 0.5)
            odds = data.get("odds", 1.5)
            confidence = data.get("confidence", 0.5)

            kelly_info = self.calculate_kelly_with_confidence(prob, odds, confidence)
            kelly_fraction = kelly_info["kelly_fraction"]

            # Calcular stake en dinero
            stake = bankroll * kelly_fraction

            optimized[parlay_type] = {
                **data,
                **kelly_info,
                "optimal_stake": round(stake, 2),
                "stake_pct": round(kelly_fraction * 100, 1),
            }

            total_allocation += kelly_fraction

        # Normalizar si suma > 100%
        if total_allocation > 1.0:
            for parlay_type in optimized:
                optimized[parlay_type]["optimal_stake"] *= (1.0 / total_allocation)
                optimized[parlay_type]["stake_pct"] /= total_allocation

        return optimized

    def expected_value(self, win_prob: float, odds: float, stake: float) -> float:
        """
        Calcula Expected Value
        EV = (win_prob × odds × stake) - stake
        """

        if win_prob < 0 or win_prob > 1 or odds < 1:
            return 0

        winning = win_prob * (odds - 1) * stake
        losing = (1 - win_prob) * stake

        return round(winning - losing, 2)

    def calculate_ev_ratio(self, win_prob: float, odds: float) -> float:
        """
        Calcula EV ratio (ROI esperado)
        EV_ratio = (win_prob × odds) - 1

        > 0 = valor positivo
        = 0 = break-even
        < 0 = valor negativo
        """

        if win_prob < 0 or win_prob > 1 or odds < 1:
            return 0

        return round((win_prob * odds) - 1, 4)


# Singleton
kelly = KellyCriterionOptimizer()


if __name__ == "__main__":
    print("[TEST] Kelly Criterion Optimizer\n")

    # Test 1: Simple Kelly
    print("TEST 1: Simple Kelly Criterion")
    kelly_val = kelly.calculate_kelly(0.55, 2.0)
    print(f"P=55%, Odds=2.0 → Kelly={kelly_val} ({kelly_val*100:.1f}% bankroll)\n")

    # Test 2: Kelly con confianza
    print("TEST 2: Kelly con confianza")
    result = kelly.calculate_kelly_with_confidence(0.62, 3.2, confidence=0.8)
    print(f"P=62%, Odds=3.2, Confidence=80%")
    print(f"  Full Kelly: {result['kelly_full']}")
    print(f"  Kelly Fraction: {result['kelly_fraction']}")
    print(f"  Stake Fraction: {result['stake_fraction']}\n")

    # Test 3: Asignación óptima
    print("TEST 3: Asignación óptima para $1000")
    parlays = {
        "ultra": {"prob": 0.78, "odds": 1.75, "confidence": 0.9},
        "conservador": {"prob": 0.62, "odds": 3.2, "confidence": 0.8},
        "balanceado": {"prob": 0.41, "odds": 6.8, "confidence": 0.6},
    }

    optimized = kelly.optimize_parlay_allocation(parlays, bankroll=1000)
    for parlay_type, allocation in optimized.items():
        print(f"{parlay_type}: ${allocation['optimal_stake']} ({allocation['stake_pct']:.1f}%)")

    print()

    # Test 4: EV
    print("TEST 4: Expected Value")
    ev = kelly.expected_value(0.55, 2.0, 100)
    ev_ratio = kelly.calculate_ev_ratio(0.55, 2.0)
    print(f"P=55%, Odds=2.0, Stake=$100")
    print(f"  EV: ${ev}")
    print(f"  EV Ratio: {ev_ratio*100:.2f}% ROI")
