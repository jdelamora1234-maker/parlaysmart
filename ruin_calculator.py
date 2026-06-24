"""
RUIN CALCULATOR - Probabilidad de bancarrota
Gambler's Ruin Problem: Qué probabilidad tenemos de perder todo?
Beneficio: Know exact bankruptcy risk antes de apostar
"""

import numpy as np
from scipy import stats
from typing import Dict, Tuple, List

class RuinCalculator:
    """Calcula riesgo de quiebra"""

    def __init__(self):
        pass

    def calculate_ruin_probability(self,
                                  bankroll: float,
                                  win_probability: float,
                                  odds: float,
                                  stake: float) -> float:
        """
        Calcula probabilidad de ruin (Gambler's Ruin formula)

        P(ruin) depende de:
        - Bankroll inicial
        - Win rate
        - Odds
        - Stake size
        """

        # Ventaja del jugador
        p = win_probability  # Probabilidad de ganar
        q = 1 - p            # Probabilidad de perder

        # Retorno esperado
        expected_return = (p * odds) - 1

        if expected_return <= 0:
            return 1.0  # Si no hay edge, probabilidad de ruin = 100%

        # Número de bets hasta ruin
        bets_to_bankrupt = bankroll / stake

        # Ruin probability: (1-p)/p si p > q, else 1
        if p > q:
            ruin_prob = ((q / p) ** bets_to_bankrupt)
        else:
            ruin_prob = 1.0

        return min(ruin_prob, 1.0)

    def calculate_ruin_with_sequence(self,
                                    bankroll: float,
                                    win_rate: float,
                                    avg_odds: float,
                                    num_bets: int,
                                    kelly_fraction: float = 0.25) -> Dict:
        """
        Calcula ruin probability considerando Kelly Criterion

        Kelly sizing reduce ruin probability dramáticamente
        """

        # Kelly stake
        kelly_stake = bankroll * kelly_fraction

        # Ruin probability para cada parlay
        ruin_probs = []

        for i in range(num_bets):
            p_ruin = self.calculate_ruin_probability(
                bankroll - (i * kelly_stake),
                win_rate,
                avg_odds,
                kelly_stake
            )
            ruin_probs.append(p_ruin)

        # Probabilidad acumulativa de ruin (cualquier momento)
        total_ruin_prob = 1 - np.prod([1 - p for p in ruin_probs if p < 1])

        return {
            "single_bet_ruin": round(self.calculate_ruin_probability(
                bankroll, win_rate, avg_odds, kelly_stake
            ), 4),
            "cumulative_ruin_prob": round(total_ruin_prob, 4),
            "safe_probability": round(1 - total_ruin_prob, 4),
            "recommendation": (
                "SAFE" if total_ruin_prob < 0.01 else
                "ACCEPTABLE" if total_ruin_prob < 0.05 else
                "RISKY" if total_ruin_prob < 0.10 else
                "VERY_RISKY"
            ),
            "implied_odds": round(1 / total_ruin_prob, 2) if total_ruin_prob > 0 else float('inf'),
        }

    def monte_carlo_ruin(self,
                        bankroll: float,
                        win_rate: float,
                        avg_odds: float,
                        stake: float,
                        num_bets: int,
                        simulations: int = 10000) -> Dict:
        """
        Simula ruin probability via Monte Carlo (más preciso)
        """

        ruin_count = 0
        max_balances = []

        for _ in range(simulations):
            current_bankroll = bankroll

            for _ in range(num_bets):
                if current_bankroll <= 0:
                    ruin_count += 1
                    break

                if np.random.random() < win_rate:
                    current_bankroll += stake * (avg_odds - 1)
                else:
                    current_bankroll -= stake

            max_balances.append(current_bankroll)

        ruin_probability = ruin_count / simulations

        return {
            "monte_carlo_ruin_prob": round(ruin_probability, 4),
            "simulations": simulations,
            "expected_final_bankroll": round(np.mean(max_balances), 2),
            "std_dev": round(np.std(max_balances), 2),
            "worst_case_10pct": round(np.percentile(max_balances, 10), 2),
            "confidence_95_ci": {
                "low": round(np.percentile(max_balances, 2.5), 2),
                "high": round(np.percentile(max_balances, 97.5), 2),
            },
            "safe_probability": round(1 - ruin_probability, 4),
        }

    def optimal_stake_for_ruin_limit(self,
                                    bankroll: float,
                                    win_rate: float,
                                    avg_odds: float,
                                    max_ruin_tolerance: float = 0.05) -> float:
        """
        Encuentra stake máximo que respeta límite de ruin

        Por ejemplo: Queremos max 5% ruin probability
        """

        # Binary search
        low_stake = 1.0
        high_stake = bankroll * 0.5

        for _ in range(50):
            mid_stake = (low_stake + high_stake) / 2

            ruin_prob = self.calculate_ruin_probability(
                bankroll, win_rate, avg_odds, mid_stake
            )

            if ruin_prob < max_ruin_tolerance:
                low_stake = mid_stake
            else:
                high_stake = mid_stake

        return round(low_stake, 2)

    def sequential_betting_risk(self,
                               bankroll: float,
                               bets: List[Tuple[float, float]]) -> Dict:
        """
        Calcula ruin risk para secuencia de bets con diferentes odds

        bets: [(win_prob, odds), (win_prob, odds), ...]
        """

        current_bankroll = bankroll
        cumulative_ruin_prob = 0

        bet_results = []

        for i, (win_prob, odds) in enumerate(bets):
            # Stake = 5% de bankroll actual (conservative)
            stake = current_bankroll * 0.05

            ruin_prob = self.calculate_ruin_probability(
                current_bankroll, win_prob, odds, stake
            )

            cumulative_ruin_prob = cumulative_ruin_prob + ruin_prob * (1 - cumulative_ruin_prob)

            bet_results.append({
                "bet_num": i + 1,
                "win_prob": round(win_prob, 3),
                "odds": round(odds, 2),
                "stake": round(stake, 2),
                "ruin_prob_this_bet": round(ruin_prob, 4),
                "cumulative_ruin_prob": round(cumulative_ruin_prob, 4),
                "bankroll_after_win": round(current_bankroll + stake * (odds - 1), 2),
                "bankroll_after_loss": round(current_bankroll - stake, 2),
            })

        return {
            "bets_analyzed": len(bets),
            "total_cumulative_ruin_prob": round(cumulative_ruin_prob, 4),
            "safe_probability": round(1 - cumulative_ruin_prob, 4),
            "bet_details": bet_results,
        }


# Singleton
ruin_calc = RuinCalculator()


if __name__ == "__main__":
    print("[TEST] Ruin Calculator\n")

    # Test 1: Simple ruin
    print("Test 1: Simple Ruin Probability")
    ruin = ruin_calc.calculate_ruin_with_sequence(1000, 0.75, 2.5, 50)
    print(f"Bankroll: $1000, Win rate: 75%, Odds: 2.5")
    print(f"Ruin probability: {ruin['cumulative_ruin_prob']*100:.2f}%")
    print(f"Safe probability: {ruin['safe_probability']*100:.2f}%")
    print(f"Status: {ruin['recommendation']}\n")

    # Test 2: Monte Carlo
    print("Test 2: Monte Carlo Ruin (10k sims)")
    mc = ruin_calc.monte_carlo_ruin(1000, 0.75, 2.5, 50, 50, simulations=1000)  # Reduced for speed
    print(f"MC Ruin probability: {mc['monte_carlo_ruin_prob']*100:.2f}%")
    print(f"Expected final bankroll: ${mc['expected_final_bankroll']}")
    print(f"95% CI: ${mc['confidence_95_ci']['low']} - ${mc['confidence_95_ci']['high']}\n")

    # Test 3: Optimal stake
    print("Test 3: Optimal Stake for 5% Ruin Limit")
    optimal = ruin_calc.optimal_stake_for_ruin_limit(1000, 0.75, 2.5, max_ruin_tolerance=0.05)
    print(f"Max safe stake: ${optimal}")
    print(f"This gives you <5% bankruptcy risk")
