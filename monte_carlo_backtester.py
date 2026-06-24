"""
MONTE CARLO BACKTESTER - Validación profunda con simulaciones
Problema: Backtest histórico = sesgo a ese histórico
Solución: Simular 10,000 posibles futuros
Beneficio: Confianza real en estadísticas (CI 95%)
"""

import random
import numpy as np
from typing import Dict, List, Tuple
import json

class MonteCarloBacktester:
    """Backtesting con simulaciones Monte Carlo"""

    def __init__(self, num_simulations: int = 10000):
        self.num_simulations = num_simulations
        self.simulation_results = []

    def run_monte_carlo(self,
                       win_rate: float,
                       avg_odds: float,
                       num_bets: int = 50,
                       bankroll: float = 1000.0,
                       stake_size: float = 50.0) -> Dict:
        """
        Corre simulaciones Monte Carlo

        Genera 10,000 posibles secuencias de bets con win_rate dado
        """

        results = {
            "input": {
                "win_rate": win_rate,
                "avg_odds": avg_odds,
                "num_bets": num_bets,
                "bankroll": bankroll,
                "stake": stake_size,
            },
            "simulations": []
        }

        bankroll_outcomes = []
        roi_outcomes = []
        max_drawdowns = []
        ruin_count = 0

        for sim in range(self.num_simulations):
            sim_bankroll = bankroll
            max_balance = bankroll

            for bet_num in range(num_bets):
                # Simular resultado
                is_win = random.random() < win_rate

                if is_win:
                    sim_bankroll += stake_size * (avg_odds - 1)
                else:
                    sim_bankroll -= stake_size

                # Rastrear máximo para drawdown
                max_balance = max(max_balance, sim_bankroll)

            # Registrar resultados
            final_roi = ((sim_bankroll - bankroll) / bankroll) * 100
            max_drawdown = ((max_balance - sim_bankroll) / max_balance) * 100 if max_balance > 0 else 0

            bankroll_outcomes.append(sim_bankroll)
            roi_outcomes.append(final_roi)
            max_drawdowns.append(max_drawdown)

            if sim_bankroll < 0:
                ruin_count += 1

        # Calcular estadísticas
        bankroll_outcomes.sort()
        roi_outcomes.sort()

        results["statistics"] = {
            "expected_final_bankroll": round(np.mean(bankroll_outcomes), 2),
            "std_dev_bankroll": round(np.std(bankroll_outcomes), 2),
            "expected_roi_pct": round(np.mean(roi_outcomes), 2),
            "median_roi_pct": round(np.median(roi_outcomes), 2),
            "confidence_interval_95": {
                "low": round(bankroll_outcomes[int(self.num_simulations * 0.025)], 2),
                "high": round(bankroll_outcomes[int(self.num_simulations * 0.975)], 2),
            },
            "worst_case_10pct": round(bankroll_outcomes[int(self.num_simulations * 0.10)], 2),
            "best_case_10pct": round(bankroll_outcomes[int(self.num_simulations * 0.90)], 2),
            "probability_of_ruin": round((ruin_count / self.num_simulations) * 100, 2),
            "average_max_drawdown_pct": round(np.mean(max_drawdowns), 2),
        }

        return results

    def compare_strategies(self, strategies: Dict[str, Dict]) -> Dict:
        """
        Compara múltiples estrategias mediante Monte Carlo

        strategies: {
            "conservative": {"win_rate": 0.60, "avg_odds": 2.5, "stake": 50},
            "aggressive": {"win_rate": 0.65, "avg_odds": 3.0, "stake": 100},
        }
        """

        comparison = {"strategies": {}}

        for strategy_name, params in strategies.items():
            result = self.run_monte_carlo(
                win_rate=params["win_rate"],
                avg_odds=params["avg_odds"],
                num_bets=params.get("num_bets", 50),
                stake_size=params["stake"]
            )

            comparison["strategies"][strategy_name] = result["statistics"]

        # Rankear por Sharpe-like ratio
        for name, stats in comparison["strategies"].items():
            if stats["std_dev_bankroll"] > 0:
                ratio = stats["expected_roi_pct"] / (stats["std_dev_bankroll"] / 1000)
                stats["risk_reward_ratio"] = round(ratio, 2)

        return comparison

    def sensitivity_analysis(self, base_win_rate: float, base_odds: float,
                           variance_range: Tuple[float, float] = (0.05, 0.15)) -> Dict:
        """
        Análisis de sensibilidad: qué pasa si win_rate es diferente

        Util para ver robustez del sistema
        """

        results = {"sensitivity": {}}

        for variance in np.arange(variance_range[0], variance_range[1], 0.01):
            adjusted_wr = base_win_rate - variance

            if adjusted_wr < 0.40:
                continue

            sim_result = self.run_monte_carlo(
                win_rate=adjusted_wr,
                avg_odds=base_odds,
                num_bets=50
            )

            results["sensitivity"][f"wr_{adjusted_wr:.2f}"] = {
                "expected_roi": sim_result["statistics"]["expected_roi_pct"],
                "probability_of_ruin": sim_result["statistics"]["probability_of_ruin"],
            }

        return results

    def calculate_required_edge(self, target_roi: float,
                               num_bets: int = 50,
                               odds: float = 2.5) -> float:
        """
        Calcula qué win_rate se necesita para lograr target ROI

        Useful para ver si sistema es viable
        """

        # Binary search para encontrar win_rate
        low, high = 0.40, 0.99

        for _ in range(50):  # 50 iteraciones
            mid = (low + high) / 2

            result = self.run_monte_carlo(
                win_rate=mid,
                avg_odds=odds,
                num_bets=num_bets
            )

            roi = result["statistics"]["expected_roi_pct"]

            if roi < target_roi:
                low = mid
            else:
                high = mid

        return round(mid, 3)

    def stress_test(self, win_rate: float, odds: float) -> Dict:
        """
        Stress test: qué pasa en peor escenario posible

        Busca el percentil 1% (worst 1% outcome)
        """

        outcomes = []

        for _ in range(self.num_simulations):
            bankroll = 1000
            for _ in range(50):
                if random.random() < win_rate:
                    bankroll += 50 * (odds - 1)
                else:
                    bankroll -= 50

            outcomes.append(bankroll)

        outcomes.sort()

        return {
            "worst_1_percent": round(outcomes[int(self.num_simulations * 0.01)], 2),
            "worst_5_percent": round(outcomes[int(self.num_simulations * 0.05)], 2),
            "worst_10_percent": round(outcomes[int(self.num_simulations * 0.10)], 2),
            "median": round(outcomes[int(self.num_simulations * 0.50)], 2),
            "best_10_percent": round(outcomes[int(self.num_simulations * 0.90)], 2),
        }


# Singleton
monte_carlo = MonteCarloBacktester()


if __name__ == "__main__":
    print("[TEST] Monte Carlo Backtester\n")

    # Test 1: Simulación simple
    print("Test 1: Monte Carlo Simulation (10k iterations)")
    result = monte_carlo.run_monte_carlo(
        win_rate=0.75,
        avg_odds=2.5,
        num_bets=50
    )

    print(f"Expected final bankroll: ${result['statistics']['expected_final_bankroll']}")
    print(f"Expected ROI: {result['statistics']['expected_roi_pct']}%")
    print(f"Probability of ruin: {result['statistics']['probability_of_ruin']}%")
    print(f"95% CI: ${result['statistics']['confidence_interval_95']['low']} - ${result['statistics']['confidence_interval_95']['high']}\n")

    # Test 2: Comparar estrategias
    print("Test 2: Strategy Comparison")
    strategies = {
        "conservative": {"win_rate": 0.70, "avg_odds": 2.2, "stake": 50},
        "aggressive": {"win_rate": 0.75, "avg_odds": 2.8, "stake": 100},
    }

    comparison = monte_carlo.compare_strategies(strategies)
    print(json.dumps(comparison, indent=2))

    # Test 3: Stress test
    print("\nTest 3: Stress Test")
    stress = monte_carlo.stress_test(0.75, 2.5)
    print(json.dumps(stress, indent=2))
