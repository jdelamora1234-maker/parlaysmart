"""
MULTI-BOOKIE MANAGER - Optimiza entre múltiples casas de apuestas
Problema: Diferentes casas tienen diferentes odds
Solución: Comparar y seleccionar mejores odds automáticamente
Beneficio: +2-3% ROI extra comparando 3-5 bookmakers
"""

from typing import Dict, List, Tuple
import json

class MultiBookieManager:
    """Gestiona múltiples casas de apuestas"""

    def __init__(self):
        self.bookies = {}
        self.registered_bookies = {
            "betfair": {"margin": 0.02, "limits": {"min": 2, "max": 500}},
            "pinnacle": {"margin": 0.01, "limits": {"min": 5, "max": 1000}},
            "bet365": {"margin": 0.04, "limits": {"min": 1, "max": 100}},
            "draftkings": {"margin": 0.05, "limits": {"min": 5, "max": 500}},
            "fanduel": {"margin": 0.05, "limits": {"min": 5, "max": 500}},
        }
        self.live_odds = {}

    def register_bookie_odds(self, bookie_name: str, match_id: str,
                            odds: Dict[str, float]):
        """Registra odds de una casa"""

        if bookie_name not in self.registered_bookies:
            return False

        key = f"{match_id}:{bookie_name}"
        self.live_odds[key] = {
            "bookie": bookie_name,
            "match_id": match_id,
            "odds": odds,
            "timestamp": None,  # timestamp real en producción
        }

        return True

    def find_best_odds(self, match_id: str, outcome: str) -> Tuple[str, float]:
        """
        Encuentra la mejor casa para un outcome específico

        Retorna: (bookie_name, best_odds)
        """

        best_bookie = None
        best_odds = 0

        for bookie_name in self.registered_bookies:
            key = f"{match_id}:{bookie_name}"
            if key in self.live_odds:
                odds_val = self.live_odds[key].get("odds", {}).get(outcome, 0)
                if odds_val > best_odds:
                    best_odds = odds_val
                    best_bookie = bookie_name

        return (best_bookie, best_odds) if best_bookie else (None, 0)

    def build_best_odds_portfolio(self, match_id: str) -> Dict[str, Tuple[str, float]]:
        """
        Construye portafolio de mejores odds

        Para cada outcome, obtiene la mejor casa
        """

        portfolio = {}

        for outcome in ["home", "draw", "away"]:
            bookie, odds = self.find_best_odds(match_id, outcome)
            if bookie:
                portfolio[outcome] = (bookie, odds)

        return portfolio

    def calculate_implied_probability(self, odds_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Calcula probabilidad implícita desde odds

        P(outcome) = 1 / odds (sin margin)
        """

        probs = {}

        for outcome, odds in odds_dict.items():
            prob = 1 / odds if odds > 0 else 0
            probs[outcome] = round(prob, 3)

        # Normalizar (odds incluyen margin)
        total = sum(probs.values())
        return {k: round(v / total, 3) for k, v in probs.items()}

    def detect_arbitrage_across_bookies(self, match_id: str) -> Dict:
        """
        Detecta oportunidades de arbitrage entre bookmakers

        Arbitrage = combinación donde guarantees profit sin importar resultado
        """

        portfolio = self.build_best_odds_portfolio(match_id)

        if len(portfolio) < 3:
            return {"arbitrage_found": False}

        # Calcular suma de probabilidades implícitas
        probs = self.calculate_implied_probability({
            outcome: odds for outcome, (_, odds) in portfolio.items()
        })

        sum_probs = sum(probs.values())

        # Arbitrage existe si sum < 1.0
        if sum_probs < 1.0:
            arb_margin = (1 - sum_probs) * 100

            return {
                "arbitrage_found": True,
                "margin_pct": round(arb_margin, 2),
                "portfolio": portfolio,
                "guaranteed_roi": round(arb_margin / (100 - arb_margin) * 100, 2),
                "example_bet": {
                    "home": round(100 * probs["home"], 2),
                    "draw": round(100 * probs["draw"], 2),
                    "away": round(100 * probs["away"], 2),
                    "total_stake": 100,
                    "profit": round(100 * arb_margin / 100, 2),
                }
            }

        return {"arbitrage_found": False}

    def optimize_stakes_across_bookies(self, match_id: str, total_bankroll: float,
                                       our_probabilities: Dict[str, float]) -> Dict[str, Dict]:
        """
        Optimiza distribución de stakes entre bookmakers

        Si tenemos edge en cada casa, apuntamos en cada una
        """

        portfolio = self.build_best_odds_portfolio(match_id)
        optimized = {}

        for outcome, (bookie, odds) in portfolio.items():
            our_prob = our_probabilities.get(outcome, 0.5)
            fair_odds = 1 / our_prob if our_prob > 0 else 0

            # Calcular edge
            edge = (fair_odds - odds) / odds if odds > 0 else 0

            if edge > 0.05:  # Solo si tenemos +5% edge
                # Kelly Criterion para este bet
                kelly_pct = (our_prob * odds - 1) / (odds - 1) * 0.25  # 25% Kelly

                stake = total_bankroll * kelly_pct
                stake = min(stake, self.registered_bookies[bookie]["limits"]["max"])
                stake = max(stake, self.registered_bookies[bookie]["limits"]["min"])

                optimized[outcome] = {
                    "bookie": bookie,
                    "odds": round(odds, 2),
                    "our_prob": round(our_prob, 3),
                    "fair_odds": round(fair_odds, 2),
                    "edge_pct": round(edge * 100, 2),
                    "recommended_stake": round(stake, 2),
                    "expected_value": round(stake * edge, 2),
                }

        return optimized

    def compare_bookies_on_match(self, match_id: str) -> Dict:
        """
        Compara todas las casas en un match

        Útil para ver quién tiene líneas distintas
        """

        comparison = {
            "match_id": match_id,
            "bookies_comparison": {}
        }

        for bookie_name in self.registered_bookies:
            key = f"{match_id}:{bookie_name}"
            if key in self.live_odds:
                odds = self.live_odds[key].get("odds", {})
                margin = self._calculate_margin(odds)

                comparison["bookies_comparison"][bookie_name] = {
                    "odds": {k: round(v, 2) for k, v in odds.items()},
                    "implied_margin": round(margin * 100, 2),
                    "best_for": [out for out in odds if self._is_best_odds(match_id, out, odds[out])]
                }

        return comparison

    def _calculate_margin(self, odds_dict: Dict[str, float]) -> float:
        """Calcula el margen implícito de una casa"""
        if not odds_dict:
            return 0

        sum_probs = sum(1 / odds for odds in odds_dict.values() if odds > 0)
        return sum_probs - 1

    def _is_best_odds(self, match_id: str, outcome: str, odds: float) -> bool:
        """Verifica si estas odds son las mejores para este outcome"""
        _, best = self.find_best_odds(match_id, outcome)
        return odds >= best

    def get_bookie_report(self, match_id: str) -> Dict:
        """Reporte completo de oportunidades entre bookies"""

        return {
            "match_id": match_id,
            "best_portfolio": self.build_best_odds_portfolio(match_id),
            "arbitrage": self.detect_arbitrage_across_bookies(match_id),
            "comparison": self.compare_bookies_on_match(match_id),
            "total_bookies_tracked": len([k for k in self.live_odds if k.startswith(match_id)])
        }


# Singleton
bookie_manager = MultiBookieManager()


if __name__ == "__main__":
    print("[TEST] Multi-Bookie Manager\n")

    # Registrar odds de diferentes casas
    bookie_manager.register_bookie_odds("betfair", "barcelona-realmadrid",
                                       {"home": 1.95, "draw": 3.20, "away": 3.50})
    bookie_manager.register_bookie_odds("pinnacle", "barcelona-realmadrid",
                                       {"home": 1.98, "draw": 3.18, "away": 3.45})
    bookie_manager.register_bookie_odds("bet365", "barcelona-realmadrid",
                                       {"home": 1.90, "draw": 3.30, "away": 3.60})

    print("✅ Registered odds from 3 bookies\n")

    # Encontrar mejores odds
    portfolio = bookie_manager.build_best_odds_portfolio("barcelona-realmadrid")
    print("Best Odds Portfolio:")
    for outcome, (bookie, odds) in portfolio.items():
        print(f"  {outcome}: {odds} @ {bookie}")

    # Detectar arbitrage
    arb = bookie_manager.detect_arbitrage_across_bookies("barcelona-realmadrid")
    print(f"\nArbitrage Status: {arb['arbitrage_found']}")

    # Optimizar stakes
    our_probs = {"home": 0.62, "draw": 0.25, "away": 0.13}
    optimized = bookie_manager.optimize_stakes_across_bookies(
        "barcelona-realmadrid", 1000, our_probs
    )
    print(f"\nOptimized Stakes:")
    import json
    print(json.dumps(optimized, indent=2))
