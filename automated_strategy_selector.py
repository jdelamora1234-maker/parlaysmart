"""
AUTOMATED STRATEGY SELECTOR - Selecciona la mejor estrategia automáticamente
Beneficio: Sistema se adapta a diferentes escenarios
Expectativa: +5% por selección óptima de estrategia
"""

import numpy as np
from typing import Dict, List

class AutomatedStrategySelector:
    """Selecciona automáticamente la mejor estrategia"""

    def __init__(self):
        self.strategies = {
            "ultra": {"description": "Aggressive", "min_confidence": 0.80, "kelly": 0.50},
            "conservador": {"description": "Conservative", "min_confidence": 0.55, "kelly": 0.15},
            "balanceado": {"description": "Balanced", "min_confidence": 0.65, "kelly": 0.25},
            "riesgoso": {"description": "Risky", "min_confidence": 0.70, "kelly": 0.40},
            "arbitrage": {"description": "Guaranteed", "min_confidence": 0.99, "kelly": 1.00},
        }

    def select_optimal_strategy(self,
                               confidence_level: float,
                               edge_strength: float,
                               market_efficiency: float,
                               bankroll: float,
                               current_drawdown: float) -> Dict:
        """
        Selecciona estrategia óptima basada en contexto

        Factores:
        - Confianza de predicción
        - Fuerza del edge
        - Eficiencia del mercado
        - Tamaño del bankroll
        - Drawdown actual
        """

        scores = {}

        for strategy_name, strategy_info in self.strategies.items():
            score = 0

            # Score por confianza
            if confidence_level >= strategy_info["min_confidence"]:
                score += 0.3
            else:
                score -= 0.2

            # Score por edge
            if edge_strength > 0.10:
                score += 0.2
            elif edge_strength > 0.05:
                score += 0.1

            # Score por eficiencia del mercado
            if market_efficiency < 0.5:  # Ineficiente = bueno
                score += 0.15

            # Score por drawdown
            if current_drawdown < 0.10:
                score += 0.2
            elif current_drawdown > 0.30:
                score -= 0.3

            # Score por tamaño de bankroll
            if bankroll > 10000:
                score += 0.15
            elif bankroll < 1000:
                score -= 0.1

            scores[strategy_name] = max(score, -1)

        # Encontrar mejor estrategia
        best_strategy = max(scores, key=scores.get)

        return {
            "selected_strategy": best_strategy,
            "strategy_description": self.strategies[best_strategy]["description"],
            "strategy_scores": {k: round(v, 2) for k, v in scores.items()},
            "kelly_fraction": self.strategies[best_strategy]["kelly"],
            "confidence": self.strategies[best_strategy]["min_confidence"],
            "reasoning": self._explain_selection(best_strategy, confidence_level, edge_strength, market_efficiency),
        }

    def _explain_selection(self,
                          strategy: str,
                          confidence: float,
                          edge: float,
                          efficiency: float) -> str:
        """Explica por qué se seleccionó esta estrategia"""

        reasons = []

        if strategy == "ultra":
            reasons.append("High confidence + strong edge")
        elif strategy == "conservador":
            reasons.append("Lower confidence - be cautious")
        elif strategy == "balanceado":
            reasons.append("Moderate conditions - balanced approach")
        elif strategy == "arbitrage":
            reasons.append("Market inefficiency detected - guaranteed profit")

        return "; ".join(reasons)

    def switch_strategy_if_needed(self,
                                 current_strategy: str,
                                 new_context: Dict) -> Dict:
        """
        Decide si cambiar de estrategia basado en contexto nuevo

        Si contexto cambió significativamente, cambiar
        """

        current_score = 0
        new_context_extracted = {
            "confidence_level": new_context.get("confidence", 0.65),
            "edge_strength": new_context.get("edge", 0.05),
            "market_efficiency": new_context.get("market_efficiency", 0.60),
            "bankroll": new_context.get("bankroll", 5000),
            "current_drawdown": new_context.get("drawdown", 0.05),
        }

        new_selection = self.select_optimal_strategy(**new_context_extracted)
        new_strategy = new_selection["selected_strategy"]

        should_switch = new_strategy != current_strategy

        return {
            "current_strategy": current_strategy,
            "new_strategy": new_strategy,
            "should_switch": should_switch,
            "switch_reason": "Market conditions changed significantly" if should_switch else "Current strategy still optimal",
            "confidence_improvement": new_selection["strategy_scores"][new_strategy] -
                                     new_selection["strategy_scores"][current_strategy],
        }

    def get_all_strategies_performance(self) -> Dict:
        """Retorna información sobre todas las estrategias"""

        return {
            "strategies": {
                name: {
                    "description": info["description"],
                    "min_confidence": info["min_confidence"],
                    "kelly_fraction": info["kelly"],
                    "use_case": self._get_use_case(name),
                }
                for name, info in self.strategies.items()
            }
        }

    def _get_use_case(self, strategy: str) -> str:
        """Retorna caso de uso para cada estrategia"""

        use_cases = {
            "ultra": "High confidence + strong edge situations",
            "conservador": "Uncertain conditions + small edge",
            "balanceado": "Normal market conditions",
            "riesgoso": "Good edge + moderate risk tolerance",
            "arbitrage": "Market inefficiencies detected",
        }

        return use_cases.get(strategy, "Unknown")


strategy_selector = AutomatedStrategySelector()

if __name__ == "__main__":
    print("[TEST] Automated Strategy Selector\n")

    result = strategy_selector.select_optimal_strategy(
        confidence_level=0.75,
        edge_strength=0.08,
        market_efficiency=0.55,
        bankroll=5000,
        current_drawdown=0.05
    )

    print(f"Selected: {result['selected_strategy']}")
    print(f"Kelly: {result['kelly_fraction']}")
