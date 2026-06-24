"""
VOLATILITY FORECASTER - Predicción de volatilidad de mercado
Usa: GARCH models + volatility clustering
Beneficio: Saber cuándo el mercado es inestable
Expectativa: +2-4% mejor timing
"""

import numpy as np
from typing import Dict, List, Tuple

class VolatilityForecaster:
    """Predice volatilidad futura del mercado"""

    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.historical_returns = []
        self.volatility_history = []

    def calculate_returns(self, odds_history: List[float]) -> List[float]:
        """Calcula retornos desde odds"""
        returns = []
        for i in range(1, len(odds_history)):
            ret = (odds_history[i] - odds_history[i-1]) / odds_history[i-1]
            returns.append(ret)
        return returns

    def estimate_volatility(self,
                           returns: List[float],
                           method: str = "realized") -> Dict:
        """
        Estima volatilidad histórica

        methods: realized (simple), ewma (exponential), garch
        """

        if not returns or len(returns) < 2:
            return {"error": "Need at least 2 returns"}

        if method == "realized":
            # Simple standard deviation
            vol = np.std(returns)
            return {
                "volatility": round(vol, 4),
                "method": "realized",
                "annualized": round(vol * np.sqrt(252), 4),
                "interpretation": (
                    "VERY_HIGH" if vol > 0.10 else
                    "HIGH" if vol > 0.05 else
                    "NORMAL" if vol > 0.02 else
                    "LOW"
                )
            }

        elif method == "ewma":
            # Exponential weighted moving average
            lambda_val = 0.94  # Standard for daily
            weighted_returns = []

            for i, ret in enumerate(returns):
                weight = (1 - lambda_val) * (lambda_val ** (len(returns) - i - 1))
                weighted_returns.append(weight * ret)

            vol = np.sqrt(sum(weighted_returns))
            return {
                "volatility": round(vol, 4),
                "method": "ewma",
                "annualized": round(vol * np.sqrt(252), 4),
            }

        return {"error": "Unknown method"}

    def detect_volatility_clustering(self,
                                    returns: List[float]) -> Dict:
        """
        Detecta volatility clustering (períodos de alta volatilidad agrupados)

        Indicador de que puede haber "shocks" en el mercado
        """

        if len(returns) < 10:
            return {"error": "Need at least 10 returns"}

        # Calcular volatilidad rolling
        window = 5
        rolling_vols = []

        for i in range(len(returns) - window + 1):
            vol = np.std(returns[i:i+window])
            rolling_vols.append(vol)

        # Detectar clustering
        high_vol = np.mean(rolling_vols) + np.std(rolling_vols)
        clusters = []
        in_cluster = False
        cluster_start = 0

        for i, vol in enumerate(rolling_vols):
            if vol > high_vol:
                if not in_cluster:
                    cluster_start = i
                    in_cluster = True
            else:
                if in_cluster:
                    clusters.append({"start": cluster_start, "end": i, "length": i - cluster_start})
                    in_cluster = False

        return {
            "clustering_detected": len(clusters) > 0,
            "number_of_clusters": len(clusters),
            "clusters": clusters,
            "average_cluster_length": round(np.mean([c["length"] for c in clusters]), 1) if clusters else 0,
            "implication": "EXPECT_CONTINUED_VOLATILITY" if clusters else "NORMAL_MARKET",
        }

    def forecast_volatility_garch(self,
                                 returns: List[float],
                                 forecast_periods: int = 5) -> Dict:
        """
        Predice volatilidad futura usando GARCH(1,1)

        Fórmula simplificada: σ²_t+1 = ω + α*r²_t + β*σ²_t
        """

        if len(returns) < 20:
            return {"error": "Need at least 20 returns"}

        try:
            from arch import arch_model

            # Fit GARCH(1,1)
            model = arch_model(returns, vol='Garch', p=1, q=1)
            result = model.fit(disp='off')

            # Forecast
            forecast = result.forecast(horizon=forecast_periods)
            variance_forecast = forecast.variance.values[-1]
            vol_forecast = np.sqrt(variance_forecast)

            return {
                "method": "GARCH(1,1)",
                "current_volatility": round(np.std(returns), 4),
                "forecast_periods": forecast_periods,
                "predicted_volatility": [round(float(v), 4) for v in vol_forecast],
                "average_forecast": round(float(np.mean(vol_forecast)), 4),
                "trend": (
                    "INCREASING" if vol_forecast[-1] > np.std(returns) else
                    "DECREASING"
                ),
            }

        except ImportError:
            return {"error": "arch library not installed", "fallback": "Use simple volatility methods"}

    def calculate_value_of_odds_changes(self,
                                       odds_movements: List[float],
                                       volatility: float) -> Dict:
        """
        Calcula si movimientos de odds son normales o anómalos

        Basado en volatilidad histórica
        """

        if not odds_movements:
            return {"error": "No movements"}

        recent_move = odds_movements[-1]
        expected_move = volatility * 3  # 3 standard deviations

        is_normal = abs(recent_move) < expected_move

        return {
            "recent_movement": round(recent_move, 4),
            "expected_movement": round(expected_move, 4),
            "is_normal": is_normal,
            "z_score": round(recent_move / max(volatility, 0.001), 2),
            "interpretation": (
                "ANOMALOUS" if abs(recent_move) > expected_move * 2 else
                "UNUSUAL" if not is_normal else
                "NORMAL"
            ),
        }

    def optimal_position_sizing_by_volatility(self,
                                             base_stake: float,
                                             current_volatility: float,
                                             normal_volatility: float = 0.03) -> Dict:
        """
        Ajusta tamaño de posición según volatilidad actual

        Alta volatilidad = posiciones más pequeñas
        """

        # Volatility adjustment
        vol_ratio = current_volatility / max(normal_volatility, 0.01)

        # Size inversely proportional to volatility
        adjusted_stake = base_stake / vol_ratio

        return {
            "base_stake": base_stake,
            "current_volatility": round(current_volatility, 4),
            "normal_volatility": round(normal_volatility, 4),
            "volatility_ratio": round(vol_ratio, 2),
            "adjusted_stake": round(adjusted_stake, 2),
            "adjustment_pct": round((adjusted_stake - base_stake) / base_stake * 100, 1),
            "recommendation": (
                "REDUCE_STAKES" if adjusted_stake < base_stake * 0.8 else
                "MAINTAIN_STAKES" if adjusted_stake > base_stake * 0.9 else
                "INCREASE_STAKES"
            ),
        }


volatility_forecaster = VolatilityForecaster()


if __name__ == "__main__":
    print("[TEST] Volatility Forecaster\n")

    returns = [0.005, 0.010, -0.003, 0.008, 0.002, -0.005, 0.015, -0.002, 0.012, 0.007]

    vol = volatility_forecaster.estimate_volatility(returns, method="realized")
    print(f"Volatility: {vol['volatility']}")
    print(f"Classification: {vol['interpretation']}\n")

    clustering = volatility_forecaster.detect_volatility_clustering(returns)
    print(f"Clustering detected: {clustering['clustering_detected']}")
