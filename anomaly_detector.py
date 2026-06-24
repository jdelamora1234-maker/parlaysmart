"""
ANOMALY DETECTOR - Detecta comportamientos anómalos en mercados
Métodos: Z-score, IQR, Isolation Forest
Beneficio: Encontrar "sharp money" y oportunidades temprano
Expectativa: +2% early detection advantage
"""

import numpy as np
from typing import Dict, List, Tuple
from collections import deque

class AnomalyDetector:
    """Detecta anomalías en odds y volúmenes"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.odds_history = deque(maxlen=window_size)
        self.volume_history = deque(maxlen=window_size)
        self.spread_history = deque(maxlen=window_size)

    def zscore_anomaly(self,
                      value: float,
                      historical_values: List[float],
                      threshold: float = 2.0) -> Dict:
        """
        Detecta anomalía usando Z-score

        Z-score > 2 = anomalía (95% de confianza)
        Z-score > 3 = anomalía crítica (99.7%)
        """

        if len(historical_values) < 2:
            return {"anomaly_detected": False}

        mean = np.mean(historical_values)
        std = np.std(historical_values)

        if std == 0:
            return {"anomaly_detected": False, "reason": "No variance"}

        zscore = (value - mean) / std

        return {
            "value": round(value, 4),
            "mean": round(mean, 4),
            "std_dev": round(std, 4),
            "zscore": round(zscore, 2),
            "anomaly_detected": abs(zscore) > threshold,
            "severity": (
                "CRITICAL" if abs(zscore) > 3.0 else
                "HIGH" if abs(zscore) > 2.5 else
                "MEDIUM" if abs(zscore) > 2.0 else
                "NORMAL"
            ),
            "direction": "ABOVE_NORMAL" if zscore > 0 else "BELOW_NORMAL",
        }

    def iqr_anomaly(self,
                   value: float,
                   historical_values: List[float]) -> Dict:
        """
        Detecta anomalía usando IQR (Interquartile Range)

        Más robusto que Z-score contra outliers extremos
        """

        if len(historical_values) < 4:
            return {"anomaly_detected": False}

        q1 = np.percentile(historical_values, 25)
        q3 = np.percentile(historical_values, 75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        is_anomaly = value < lower_bound or value > upper_bound

        return {
            "value": round(value, 4),
            "q1": round(q1, 4),
            "q3": round(q3, 4),
            "iqr": round(iqr, 4),
            "lower_bound": round(lower_bound, 4),
            "upper_bound": round(upper_bound, 4),
            "anomaly_detected": is_anomaly,
            "distance_from_bounds": round(
                min(abs(value - lower_bound), abs(value - upper_bound)), 4
            ),
        }

    def detect_odds_spike(self,
                         current_odds: Dict[str, float],
                         previous_odds: Dict[str, float],
                         threshold_pct: float = 0.05) -> Dict:
        """
        Detecta cambios anómalos de odds (sharp moves)

        Sharp move = cambio > 5% en corto tiempo
        """

        spikes = {}

        for outcome in current_odds:
            curr = current_odds.get(outcome, 0)
            prev = previous_odds.get(outcome, 0)

            if prev > 0:
                change_pct = abs((curr - prev) / prev)

                if change_pct > threshold_pct:
                    spikes[outcome] = {
                        "previous_odds": round(prev, 2),
                        "current_odds": round(curr, 2),
                        "change_pct": round(change_pct * 100, 2),
                        "direction": "UP" if curr > prev else "DOWN",
                        "sharp_money_signal": "YES" if change_pct > 0.10 else "POSSIBLE",
                    }

        return {
            "spikes_detected": len(spikes) > 0,
            "spike_count": len(spikes),
            "spikes": spikes,
            "action": "FOLLOW_SHARPS" if spikes else "MONITOR",
        }

    def detect_volume_anomaly(self,
                             current_volume: float,
                             volume_history: List[float],
                             threshold_multiplier: float = 2.0) -> Dict:
        """
        Detecta volumen anómalo

        Volumen 2x normal = sharp money entrando
        """

        if not volume_history:
            return {"anomaly_detected": False}

        avg_volume = np.mean(volume_history)
        median_volume = np.median(volume_history)

        volume_ratio = current_volume / max(avg_volume, 1)

        return {
            "current_volume": round(current_volume, 2),
            "average_volume": round(avg_volume, 2),
            "median_volume": round(median_volume, 2),
            "volume_ratio": round(volume_ratio, 2),
            "anomaly_detected": volume_ratio > threshold_multiplier,
            "interpretation": (
                "EXTREME" if volume_ratio > 3.0 else
                "HIGH" if volume_ratio > 2.0 else
                "NORMAL"
            ),
            "sharp_money_likelihood": round(min(volume_ratio - 1.0, 1.0), 2),
        }

    def isolation_forest_anomaly(self,
                                current_values: Dict[str, float],
                                historical_data: List[Dict[str, float]]) -> Dict:
        """
        Usa Isolation Forest para detectar anomalías multidimensionales

        Detecta patrones anómalos donde múltiples variables se comportan inusualmente
        """

        if len(historical_data) < 10:
            return {"error": "Need more historical data"}

        try:
            from sklearn.ensemble import IsolationForest

            # Preparar datos
            features = []
            for item in historical_data:
                features.append(list(item.values()))

            # Entrenar Isolation Forest
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            iso_forest.fit(features)

            # Predecir
            current_vector = list(current_values.values())
            prediction = iso_forest.predict([current_vector])[0]
            anomaly_score = iso_forest.score_samples([current_vector])[0]

            return {
                "is_anomaly": prediction == -1,
                "anomaly_score": round(float(anomaly_score), 4),  # Negativo = anomalía
                "confidence": round(abs(float(anomaly_score)), 3),
                "interpretation": (
                    "CRITICAL_ANOMALY" if anomaly_score < -0.5 else
                    "MODERATE_ANOMALY" if anomaly_score < 0 else
                    "NORMAL"
                ),
            }

        except ImportError:
            return {"error": "sklearn not installed"}

    def detect_coordinated_movement(self,
                                   odds_movements: Dict[str, List[float]]) -> Dict:
        """
        Detecta si múltiples outcomes se mueven de forma coordinada

        Coordinación = múltiples bookies ajustando a la vez = sharp money
        """

        correlations = {}

        outcomes = list(odds_movements.keys())

        for i, outcome1 in enumerate(outcomes):
            for outcome2 in outcomes[i+1:]:
                values1 = np.array(odds_movements[outcome1])
                values2 = np.array(odds_movements[outcome2])

                if len(values1) > 1 and len(values2) > 1:
                    correlation = np.corrcoef(values1, values2)[0, 1]
                    correlations[f"{outcome1}_{outcome2}"] = round(correlation, 3)

        # Detectar correlación negativa fuerte (típico de sharp money)
        strong_negative = {
            k: v for k, v in correlations.items() if v < -0.7
        }

        return {
            "correlations": correlations,
            "strong_negative_correlations": strong_negative,
            "coordinated_movement_detected": len(strong_negative) > 0,
            "implication": "SHARP_MONEY_CONFIRMED" if strong_negative else "NORMAL_MOVEMENT",
        }

    def generate_alert(self, anomaly_type: str, severity: str, details: Dict) -> Dict:
        """Genera alerta cuando se detecta anomalía"""

        return {
            "alert_type": anomaly_type,
            "severity": severity,
            "timestamp": str(__import__('datetime').datetime.now()),
            "details": details,
            "recommended_action": (
                "IMMEDIATE_ACTION" if severity == "CRITICAL" else
                "MONITOR_CLOSELY" if severity == "HIGH" else
                "WATCH"
            ),
        }


# Singleton
anomaly_detector = AnomalyDetector()


if __name__ == "__main__":
    print("[TEST] Anomaly Detector\n")

    # Test Z-score
    history = [1.90, 1.92, 1.95, 1.93, 1.94, 1.91, 1.89, 2.10]  # Última es anomalía
    zscore = anomaly_detector.zscore_anomaly(2.10, history[:-1])
    print(f"Z-score anomaly: {zscore['anomaly_detected']}")
    print(f"Severity: {zscore['severity']}\n")

    # Test odds spike
    old_odds = {"home": 1.95, "draw": 3.20, "away": 3.50}
    new_odds = {"home": 1.75, "draw": 3.20, "away": 3.80}  # Home dropped 10%
    spikes = anomaly_detector.detect_odds_spike(new_odds, old_odds)
    print(f"Spikes detected: {spikes['spikes_detected']}")
    print(f"Action: {spikes['action']}")
