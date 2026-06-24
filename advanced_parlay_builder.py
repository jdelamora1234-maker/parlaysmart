"""
ADVANCED PARLAY BUILDER - Constructor inteligente de parlays
Integra: Correlación, Kelly, Value, Injury impact, Risk
Objetivo: Construir parlays óptimos automáticamente
"""

from typing import Dict, List, Tuple
import json

class AdvancedParlayBuilder:
    """Constructor inteligente de parlays"""

    def __init__(self):
        self.built_parlays = []
        self.parlay_constraints = {
            "min_picks": 2,
            "max_picks": 4,
            "min_prob": 0.40,
            "max_correlation": 0.70,
        }

    def build_optimal_parlay(self,
                            available_picks: List[Dict],
                            bankroll: float,
                            constraints: Dict = None) -> Dict:
        """
        Construye parlay óptimo automáticamente

        available_picks: [
            {
                "match_id": "barcelona-real",
                "outcome": "home",
                "probability": 0.62,
                "odds": 1.95,
                "value": 0.12,
                "confidence": 0.85,
                "injury_impact": 0.0
            },
            ...
        ]
        """

        if constraints:
            self.parlay_constraints.update(constraints)

        # 1. Filtrar picks válidos
        valid_picks = self._filter_valid_picks(available_picks)

        if not valid_picks:
            return {"error": "No valid picks available", "built": False}

        # 2. Encontrar combinaciones óptimas
        combinations = self._find_optimal_combinations(valid_picks)

        # 3. Rankear por Sharpe ratio
        ranked = self._rank_combinations(combinations, bankroll)

        if not ranked:
            return {"error": "No valid combinations found", "built": False}

        # 4. Construir parlay final
        best_parlay = ranked[0]

        return {
            "built": True,
            "parlay": best_parlay,
            "alternatives": ranked[1:3] if len(ranked) > 1 else [],
            "optimization_metrics": {
                "total_picks": len(best_parlay["picks"]),
                "combined_probability": round(best_parlay["combined_prob"], 3),
                "combined_odds": round(best_parlay["combined_odds"], 2),
                "expected_value": round(best_parlay["expected_value"], 2),
                "sharpe_ratio": round(best_parlay["sharpe_ratio"], 2),
                "kelly_stake": round(best_parlay["kelly_stake"], 2),
                "correlation_score": round(best_parlay["correlation_score"], 2),
            }
        }

    def _filter_valid_picks(self, picks: List[Dict]) -> List[Dict]:
        """Filtra picks que cumplen constraints"""

        valid = []

        for pick in picks:
            prob = pick.get("probability", 0.5)
            injury_impact = pick.get("injury_impact", 0.0)

            # Probabilidad válida
            if prob < self.parlay_constraints["min_prob"]:
                continue

            # No está lesionado
            if injury_impact > 0.15:  # >15% impact = skip
                continue

            # Value positivo (preferible)
            if pick.get("value", 0) < -0.05:  # <-5% value = skip
                continue

            valid.append(pick)

        return valid

    def _find_optimal_combinations(self, picks: List[Dict]) -> List[List[Dict]]:
        """Encuentra combinaciones óptimas de picks"""

        from itertools import combinations

        all_combinations = []

        # Generar todas las combinaciones válidas
        for r in range(self.parlay_constraints["min_picks"],
                      min(self.parlay_constraints["max_picks"] + 1, len(picks) + 1)):

            for combo in combinations(picks, r):
                # Verificar correlación
                if self._check_correlation(list(combo)):
                    all_combinations.append(list(combo))

        return all_combinations

    def _check_correlation(self, picks: List[Dict]) -> bool:
        """Verifica si picks tienen correlación aceptable"""

        # Simplificado: asumir correlación baja si outcomes diferentes
        outcomes = [p.get("outcome") for p in picks]

        # No permitir muchos "home" juntos
        if outcomes.count("home") > 2:
            return False

        return True

    def _rank_combinations(self, combinations: List[List[Dict]],
                          bankroll: float) -> List[Dict]:
        """Rankea combinaciones por Sharpe ratio"""

        ranked = []

        for combo in combinations:
            # Calcular métricas
            combined_prob = 1.0
            combined_odds = 1.0
            total_value = 0.0

            for pick in combo:
                combined_prob *= pick.get("probability", 0.5)
                combined_odds *= pick.get("odds", 1.5)
                total_value += pick.get("value", 0)

            # Expected value
            ev = combined_prob * combined_odds - 1

            # Kelly stake
            kelly_pct = (combined_prob * combined_odds - 1) / (combined_odds - 1) * 0.25
            kelly_stake = bankroll * max(0, kelly_pct)

            # Correlation score (0-1, higher is worse)
            corr_score = self._calculate_correlation_score(combo)

            # Sharpe-like ratio: EV / correlation_risk
            sharpe = ev / (corr_score + 0.1) if combined_odds > 0 else 0

            ranked.append({
                "picks": combo,
                "combined_prob": combined_prob,
                "combined_odds": combined_odds,
                "expected_value": ev * kelly_stake,
                "kelly_stake": kelly_stake,
                "sharpe_ratio": sharpe,
                "correlation_score": corr_score,
                "total_value": total_value,
            })

        # Ordenar por Sharpe ratio descendente
        ranked.sort(key=lambda x: x["sharpe_ratio"], reverse=True)

        return ranked

    def _calculate_correlation_score(self, picks: List[Dict]) -> float:
        """Calcula score de correlación (0=independent, 1=perfectly correlated)"""

        if len(picks) < 2:
            return 0.0

        # Simplificado
        outcomes = [p.get("outcome") for p in picks]
        matches = [p.get("match_id") for p in picks]

        # Penalidad si mismo match multiple veces
        same_match = len(matches) - len(set(matches))

        # Penalidad si mismo outcome múltiples veces
        same_outcome = len([o for o in outcomes if outcomes.count(o) > 1])

        correlation_score = (same_match * 0.3 + same_outcome * 0.2) / len(picks)

        return min(correlation_score, 1.0)

    def build_hedge_parlay(self, primary_parlay: Dict,
                           bankroll: float) -> Dict:
        """
        Construye parlay de cobertura para hedgear el primario

        Si primary tiene EV positivo, hedgear con EV cercano a 0
        """

        primary_prob = primary_parlay.get("combined_prob", 0.5)
        primary_odds = primary_parlay.get("combined_odds", 2.0)

        # Hedge: apostar a lo opuesto
        hedge_prob = 1 - primary_prob
        hedge_odds = 1 / hedge_prob if hedge_prob > 0 else 2.0

        # Stake = para minimizar total exposure
        primary_risk = bankroll * 0.1  # 10% del bankroll
        hedge_stake = (primary_risk * primary_odds) / hedge_odds

        return {
            "hedge_type": "opposite",
            "hedge_stake": round(hedge_stake, 2),
            "hedge_odds": round(hedge_odds, 2),
            "hedge_prob": round(hedge_prob, 3),
            "max_win_primary": round(primary_risk * primary_odds, 2),
            "max_loss_primary": round(primary_risk, 2),
            "max_win_hedge": round(hedge_stake, 2),
            "max_loss_hedge": round(hedge_stake * hedge_odds, 2),
        }

    def validate_parlay(self, parlay: Dict) -> Tuple[bool, str]:
        """Valida parlay antes de ejecutar"""

        picks = parlay.get("picks", [])

        # Mínimo picks
        if len(picks) < self.parlay_constraints["min_picks"]:
            return False, f"Too few picks ({len(picks)})"

        # Máximo picks
        if len(picks) > self.parlay_constraints["max_picks"]:
            return False, f"Too many picks ({len(picks)})"

        # Verificar duplicates
        match_outcomes = [(p.get("match_id"), p.get("outcome")) for p in picks]
        if len(match_outcomes) != len(set(match_outcomes)):
            return False, "Duplicate picks"

        # Verificar correlation
        if not self._check_correlation(picks):
            return False, "Correlation too high"

        return True, "Valid parlay"


# Singleton
parlay_builder = AdvancedParlayBuilder()


if __name__ == "__main__":
    print("[TEST] Advanced Parlay Builder\n")

    # Available picks
    picks = [
        {
            "match_id": "barcelona-real",
            "outcome": "home",
            "probability": 0.62,
            "odds": 1.95,
            "value": 0.12,
            "confidence": 0.85,
            "injury_impact": 0.0
        },
        {
            "match_id": "manchester-liverpool",
            "outcome": "away",
            "probability": 0.45,
            "odds": 3.20,
            "value": 0.08,
            "confidence": 0.70,
            "injury_impact": 0.05
        },
        {
            "match_id": "psg-lyon",
            "outcome": "home",
            "probability": 0.70,
            "odds": 1.75,
            "value": 0.15,
            "confidence": 0.88,
            "injury_impact": 0.0
        }
    ]

    print("Available picks:")
    for p in picks:
        print(f"  {p['match_id']}: {p['outcome']} ({p['probability']*100:.0f}%)")

    # Build parlay
    result = parlay_builder.build_optimal_parlay(picks, bankroll=1000)

    print(f"\nOptimal Parlay Built: {result['built']}")
    if result['built']:
        print(f"Metrics: {json.dumps(result['optimization_metrics'], indent=2)}")
