"""
MARKET MAKING ENGINE - Generar propias líneas de apuestas
Beneficio: Arbitrage opportunities vs market
Estrategia: Ofrecer líneas ligeramente diferentes para capturar valor
"""

from typing import Dict, Tuple
import numpy as np

class MarketMakingEngine:
    """Genera líneas propias de apuestas"""

    def __init__(self):
        self.our_lines = {}
        self.market_lines = {}
        self.spread_history = []

    def calculate_fair_odds_from_analysis(self,
                                         probabilities: Dict[str, float],
                                         volatility: float = 0.02) -> Dict[str, float]:
        """
        Calcula fair odds desde nuestras probabilidades

        probabilities: {"home": 0.62, "draw": 0.25, "away": 0.13}
        volatility: cuánto mercado fluctúa (2-5%)
        """

        fair_odds = {}

        for outcome, prob in probabilities.items():
            if prob > 0:
                # Fair odds = 1 / probability
                fair = 1 / prob

                # Ajustar por volatilidad
                adjusted = fair * (1 - volatility)

                fair_odds[outcome] = round(adjusted, 2)

        return fair_odds

    def calculate_trading_margins(self,
                                 fair_odds: Dict[str, float],
                                 margin_pct: float = 0.03) -> Dict[str, float]:
        """
        Calcula nuestras líneas aplicando margen

        Margen típico: 2-5% (nosotros usamos 3%)
        """

        our_lines = {}

        for outcome, odds in fair_odds.items():
            # Aplicar margen: reducir odds ligeramente para nosotros
            # (make it harder for customer to win)
            our_odds = odds * (1 - margin_pct)

            our_lines[outcome] = round(our_odds, 2)

        return our_lines

    def detect_sharp_opportunities(self,
                                  our_lines: Dict[str, float],
                                  market_lines: Dict[str, float]) -> Dict[str, Dict]:
        """
        Detecta oportunidades de valor entre nuestras líneas y mercado

        Si nuestras líneas son MEJORES que mercado = oportunidad
        """

        opportunities = {}

        for outcome in our_lines:
            our_odds = our_lines.get(outcome, 0)
            market_odds = market_lines.get(outcome, 0)

            if our_odds > 0 and market_odds > 0:
                # Si nuestras odds son MAYORES = mejor para apostador
                value = (our_odds - market_odds) / market_odds

                if value > 0.02:  # +2% value
                    opportunities[outcome] = {
                        "our_odds": our_odds,
                        "market_odds": market_odds,
                        "value_pct": round(value * 100, 2),
                        "action": "OFFER" if value > 0.05 else "AVOID",
                    }

        return opportunities

    def dynamic_line_adjustment(self,
                              base_odds: Dict[str, float],
                              action_flow: Dict[str, float],
                              max_adjustment: float = 0.10) -> Dict[str, float]:
        """
        Ajusta líneas dinámicamente basado en action flow

        action_flow: cuánto dinero entra en cada outcome
        {"home": 0.70, "draw": 0.15, "away": 0.15}

        Si mucho dinero en un lado = reducir esos odds
        """

        adjusted = {}

        for outcome, odds in base_odds.items():
            action = action_flow.get(outcome, 0.33)

            # Si mucho action (>40%), reducir odds
            adjustment = max(0, (action - 0.35) * 0.5)
            adjustment = min(adjustment, max_adjustment)

            adjusted_odds = odds * (1 - adjustment)

            adjusted[outcome] = round(adjusted_odds, 2)

        return adjusted

    def calculate_liability(self,
                           lines: Dict[str, float],
                           bets: Dict[str, float]) -> Dict[str, float]:
        """
        Calcula nuestra exposición (liability) a cada outcome

        liability = si outcome gana, cuánto perdemos

        bets: {"home": 1000, "draw": 500, "away": 300}  (dinero apostado)
        """

        liability = {}

        for outcome in lines:
            amount_bet = bets.get(outcome, 0)
            odds = lines.get(outcome, 1)

            # Si ganan, pagamos: amount_bet * odds
            max_payout = amount_bet * odds

            liability[outcome] = round(max_payout, 2)

        return liability

    def hedging_strategy(self,
                        liability: Dict[str, float],
                        hedging_budget: float) -> Dict[str, Dict]:
        """
        Sugiere hedging para balancear exposición

        Si liability en "home" es muy alta, hedgear apostando a otros outcomes
        """

        hedges = {}

        max_liability = max(liability.values()) if liability else 0
        others_liability = sum(v for k, v in liability.items())

        for outcome, exposure in liability.items():
            if exposure > others_liability * 0.6:  # Si > 60% del total
                # Hedgear este outcome

                # Calcular stake para hedging
                # Objetivo: reducir exposure a 50/50
                excess = exposure - max_liability * 0.5
                hedge_stake = min(excess / 2, hedging_budget / 2)

                hedges[outcome] = {
                    "current_liability": round(exposure, 2),
                    "suggested_hedge_stake": round(hedge_stake, 2),
                    "new_liability_after_hedge": round(exposure - hedge_stake, 2),
                    "goal": "Balance exposure"
                }

        return hedges

    def vigorish_calculation(self,
                            odds_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Calcula vigorish (commisión implícita)

        Sum of implied probabilities > 1 = vigorish
        """

        implied_probs = {k: 1/v for k, v in odds_dict.items() if v > 0}

        total_prob = sum(implied_probs.values())
        vigorish = (total_prob - 1) * 100

        return {
            "implied_probs": {k: round(v, 3) for k, v in implied_probs.items()},
            "total_probability": round(total_prob, 3),
            "vigorish_pct": round(vigorish, 2),
            "fair_vigorish": round(vigorish / total_prob * 100, 2),
        }

    def optimal_line_pricing(self,
                            fair_probs: Dict[str, float],
                            competitor_odds: Dict[str, float],
                            target_margin: float = 0.03) -> Dict[str, float]:
        """
        Calcula líneas óptimas para competir con otros bookies

        Balancea: Margen vs competitividad
        """

        optimal_odds = {}

        for outcome in fair_probs:
            fair_prob = fair_probs.get(outcome, 0.33)
            comp_odds = competitor_odds.get(outcome, 2.0)

            # Fair odds
            fair_odds = 1 / fair_prob if fair_prob > 0 else 2.0

            # Nuestra estrategia: ofrecer ligeramente peor que competidor
            # pero mejor que super-fair (que cuesta $$ aceptar)
            our_odds = fair_odds * (1 - target_margin)

            # Si competitor tiene mucho mejor: acercarse
            if comp_odds > fair_odds:
                our_odds = min(our_odds, comp_odds * 0.95)

            optimal_odds[outcome] = round(our_odds, 2)

        return optimal_odds


# Singleton
market_maker = MarketMakingEngine()


if __name__ == "__main__":
    print("[TEST] Market Making Engine\n")

    # Test 1: Fair odds
    print("Test 1: Fair Odds Calculation")
    probs = {"home": 0.62, "draw": 0.25, "away": 0.13}
    fair = market_maker.calculate_fair_odds_from_analysis(probs)
    print(f"Probabilities: {probs}")
    print(f"Fair odds: {fair}\n")

    # Test 2: Our lines
    print("Test 2: Our Trading Lines (3% margin)")
    our_lines = market_maker.calculate_trading_margins(fair)
    print(f"Our lines: {our_lines}\n")

    # Test 3: Detect opportunities
    print("Test 3: Detect Opportunities vs Market")
    market = {"home": 1.98, "draw": 3.15, "away": 3.60}
    opps = market_maker.detect_sharp_opportunities(our_lines, market)
    print(f"Market lines: {market}")
    print(f"Opportunities: {opps}\n")

    # Test 4: Liability
    print("Test 4: Calculate Liability")
    bets = {"home": 1000, "draw": 500, "away": 300}
    liability = market_maker.calculate_liability(our_lines, bets)
    print(f"Bets: {bets}")
    print(f"Liability: {liability}")
