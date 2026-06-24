"""
MARKET EFFICIENCY ANALYZER - Mide si el mercado es eficiente
Usa: Análisis de oportunidades de arbitrage y value betting
Beneficio: Saber cuándo el mercado está desinformado
Expectativa: +2-3% cuando mercado es ineficiente
"""

import numpy as np
from typing import Dict, List
from collections import deque

class MarketEfficiencyAnalyzer:
    """Mide eficiencia del mercado de apuestas"""

    def __init__(self, lookback_window: int = 100):
        self.lookback_window = lookback_window
        self.arbitrage_opportunities = deque(maxlen=lookback_window)
        self.value_opportunities = deque(maxlen=lookback_window)
        self.odds_changes = deque(maxlen=lookback_window)

    def calculate_market_implied_probability(self,
                                            odds: Dict[str, float]) -> Dict[str, float]:
        """
        Calcula probabilidad implícita del mercado

        Suma > 1 = mercado ineficiente (vigorish)
        """

        implied = {}
        total = 0

        for outcome, odd in odds.items():
            prob = 1 / odd if odd > 0 else 0
            implied[outcome] = prob
            total += prob

        return {
            "implied_probabilities": {k: round(v, 3) for k, v in implied.items()},
            "total_implied": round(total, 3),
            "vigorish": round((total - 1) * 100, 2) if total > 0 else 0,
            "efficient": total == 1.0,
            "efficiency_level": (
                "PERFECT" if abs(total - 1.0) < 0.01 else
                "EFFICIENT" if total < 1.05 else
                "SLIGHT_INEFFICIENCY" if total < 1.15 else
                "SIGNIFICANT_INEFFICIENCY"
            ),
        }

    def detect_line_shopping_opportunity(self,
                                        bookmaker_odds: Dict[str, Dict[str, float]]) -> Dict:
        """
        Detecta si hay mejor odds en algún bookie

        Diferencia > 2% entre bookies = opportunity
        """

        opportunities = {}
        outcomes = list(next(iter(bookmaker_odds.values())).keys())

        for outcome in outcomes:
            odds_list = []

            for bookie, odds_dict in bookmaker_odds.items():
                odd = odds_dict.get(outcome, 0)
                if odd > 0:
                    odds_list.append({"bookie": bookie, "odds": odd})

            if len(odds_list) >= 2:
                odds_list.sort(key=lambda x: x["odds"], reverse=True)

                best_odd = odds_list[0]["odds"]
                worst_odd = odds_list[-1]["odds"]
                improvement_pct = (best_odd - worst_odd) / worst_odd * 100

                if improvement_pct > 2.0:  # > 2% improvement
                    opportunities[outcome] = {
                        "best_bookie": odds_list[0]["bookie"],
                        "best_odds": round(best_odd, 2),
                        "worst_bookie": odds_list[-1]["bookie"],
                        "worst_odds": round(worst_odd, 2),
                        "improvement_pct": round(improvement_pct, 2),
                    }

        return {
            "opportunities_found": len(opportunities) > 0,
            "number_of_opportunities": len(opportunities),
            "opportunities": opportunities,
            "implication": "INEFFICIENT_MARKET" if opportunities else "EFFICIENT_MARKET",
        }

    def measure_informational_efficiency(self,
                                        news_events: List[Dict],
                                        odds_changes: List[Dict]) -> Dict:
        """
        Mide qué tan rápido el mercado reacciona a noticias

        Mercado eficiente = reacciona inmediatamente
        Mercado ineficiente = reacciona lentamente o no reacciona
        """

        if not news_events or not odds_changes:
            return {"error": "Need news events and odds changes"}

        # Simular: evento de noticia → cambio de odds
        # Eficiencia = cuán cercano es el cambio de odds al cambio teórico esperado

        total_unexplained = 0
        reactions = []

        for news in news_events:
            expected_move = news.get("expected_odds_move", 0.05)

            # Encontrar cambio de odds más cercano en tiempo
            closest_move = None
            min_time_diff = float('inf')

            for move in odds_changes:
                time_diff = abs(
                    (news.get("timestamp", "") > move.get("timestamp", ""))
                )
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_move = move.get("actual_odds_move", 0)

            if closest_move is not None:
                unexplained = abs(expected_move - closest_move)
                total_unexplained += unexplained
                reactions.append(unexplained)

        # Eficiencia = 1 - (unexplained / expected)
        if total_unexplained > 0:
            efficiency = max(0, 1 - (np.mean(reactions) / 0.1))  # 10% baseline
        else:
            efficiency = 1.0

        return {
            "informational_efficiency": round(efficiency, 3),
            "efficiency_rating": (
                "HIGHLY_EFFICIENT" if efficiency > 0.8 else
                "EFFICIENT" if efficiency > 0.6 else
                "MODERATELY_INEFFICIENT" if efficiency > 0.4 else
                "HIGHLY_INEFFICIENT"
            ),
            "average_reaction_delay": round(np.mean([r.get("delay_seconds", 0) for r in reactions]) if reactions else 0, 1),
            "opportunity_window": "LARGE" if efficiency < 0.5 else "SMALL",
        }

    def calculate_sharp_money_flow(self,
                                  volume_by_bookie: Dict[str, float],
                                  odds_by_bookie: Dict[str, float]) -> Dict:
        """
        Detecta si sharp money (dinero informado) entra

        Sharp money:
        - Entra en bookies que ofrecen mejores odds
        - Causa cambios de odds grandes
        """

        # Calcular weighted average odds
        total_volume = sum(volume_by_bookie.values())

        if total_volume == 0:
            return {"error": "No volume"}

        # Dónde está concentrado el dinero
        volume_distribution = {
            b: v / total_volume for b, v in volume_by_bookie.items()
        }

        # Dónde están los mejores odds
        best_bookie = max(odds_by_bookie, key=odds_by_bookie.get)
        best_odds_pct = odds_by_bookie[best_bookie]

        # Si dinero concentrado en mejores odds = sharp money
        sharp_volume = volume_distribution.get(best_bookie, 0)

        return {
            "sharp_money_detected": sharp_volume > 0.4,  # > 40% en best odds
            "concentration_pct": round(sharp_volume * 100, 1),
            "best_bookie": best_bookie,
            "best_odds": round(best_odds_pct, 2),
            "sharp_money_signal": (
                "VERY_STRONG" if sharp_volume > 0.6 else
                "STRONG" if sharp_volume > 0.5 else
                "MODERATE" if sharp_volume > 0.4 else
                "WEAK"
            ),
        }

    def estimate_market_edge(self,
                            our_prediction: float,
                            market_odds: float) -> Dict:
        """
        Estima ventaja del mercado

        edge = si nuestra probabilidad > probabilidad implícita
        """

        market_implied = 1 / market_odds

        edge = our_prediction - market_implied
        edge_pct = edge * 100

        # ROI esperado
        expected_roi = (our_prediction * market_odds) - 1

        return {
            "our_prediction": round(our_prediction, 3),
            "market_implied": round(market_implied, 3),
            "edge": round(edge, 3),
            "edge_pct": round(edge_pct, 2),
            "expected_roi": round(expected_roi, 3),
            "edge_quality": (
                "EXCELLENT" if edge_pct > 10 else
                "VERY_GOOD" if edge_pct > 5 else
                "GOOD" if edge_pct > 2 else
                "FAIR" if edge_pct > 0 else
                "NO_EDGE"
            ),
            "bet_recommendation": "BET" if expected_roi > 0.05 else "PASS",
        }

    def assess_overall_market_efficiency(self) -> Dict:
        """Reporte general de eficiencia del mercado"""

        arbs_found = len(self.arbitrage_opportunities)
        value_found = len(self.value_opportunities)
        avg_arb_margin = (
            np.mean([a.get("margin", 0) for a in self.arbitrage_opportunities])
            if self.arbitrage_opportunities else 0
        )

        efficiency = 1 - min(avg_arb_margin / 0.05, 1)  # 5% baseline

        return {
            "arbitrages_found": arbs_found,
            "value_bets_found": value_found,
            "average_arb_margin": round(avg_arb_margin, 4),
            "estimated_efficiency": round(efficiency, 3),
            "market_status": (
                "HIGHLY_EFFICIENT" if efficiency > 0.95 else
                "EFFICIENT" if efficiency > 0.80 else
                "MODERATELY_INEFFICIENT" if efficiency > 0.60 else
                "HIGHLY_INEFFICIENT"
            ),
            "profit_opportunity": "SIGNIFICANT" if arbs_found + value_found > 5 else "MODERATE" if arbs_found + value_found > 2 else "LIMITED",
        }


market_efficiency = MarketEfficiencyAnalyzer()


if __name__ == "__main__":
    print("[TEST] Market Efficiency Analyzer\n")

    # Test implied probability
    odds = {"home": 1.95, "draw": 3.20, "away": 3.50}
    efficiency = market_efficiency.calculate_market_implied_probability(odds)
    print(f"Vigorish: {efficiency['vigorish']}%")
    print(f"Efficiency: {efficiency['efficiency_level']}\n")

    # Test edge calculation
    edge = market_efficiency.estimate_market_edge(0.65, 1.95)
    print(f"Our edge: {edge['edge_pct']}%")
    print(f"Recommendation: {edge['bet_recommendation']}")
