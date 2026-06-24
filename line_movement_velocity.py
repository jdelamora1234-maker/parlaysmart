"""
LINE MOVEMENT VELOCITY DETECTOR - Detecta velocidad de cambio de líneas
Beneficio: Identifica cuándo hay sharp money activo
Expectativa: +2-3% timing advantage
"""

import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta

class LineMovementVelocity:
    """Detecta velocidad y dirección de cambios de líneas"""

    def __init__(self):
        self.movement_history = {}

    def calculate_velocity(self,
                          historical_odds: List[float],
                          timestamps: List[str]) -> Dict:
        """
        Calcula velocidad de cambio de odds

        velocity = cambio de odds / tiempo
        """

        if len(historical_odds) < 2:
            return {"error": "Need at least 2 data points"}

        velocities = []
        time_diffs = []

        for i in range(1, len(historical_odds)):
            # Cambio de odds
            change = historical_odds[i] - historical_odds[i-1]

            # Tiempo entre cambios
            try:
                t1 = datetime.fromisoformat(timestamps[i-1])
                t2 = datetime.fromisoformat(timestamps[i])
                time_diff = (t2 - t1).total_seconds() / 60  # minutos
            except:
                time_diff = 1

            if time_diff > 0:
                velocity = change / time_diff
                velocities.append(velocity)
                time_diffs.append(time_diff)

        avg_velocity = np.mean(velocities) if velocities else 0
        max_velocity = max(velocities) if velocities else 0

        return {
            "average_velocity": round(avg_velocity, 4),
            "max_velocity": round(max_velocity, 4),
            "velocity_intensity": (
                "EXTREME" if abs(max_velocity) > 0.05 else
                "HIGH" if abs(max_velocity) > 0.02 else
                "MODERATE" if abs(max_velocity) > 0.01 else
                "LOW"
            ),
            "direction": "UP" if avg_velocity > 0 else "DOWN",
            "data_points": len(velocities),
        }

    def detect_acceleration(self,
                           velocities: List[float]) -> Dict:
        """
        Detecta si la velocidad está acelerando

        Aceleración = cambio en la velocidad
        """

        if len(velocities) < 2:
            return {"error": "Need at least 2 velocities"}

        acceleration = []

        for i in range(1, len(velocities)):
            acc = velocities[i] - velocities[i-1]
            acceleration.append(acc)

        avg_acc = np.mean(acceleration)

        return {
            "average_acceleration": round(avg_acc, 5),
            "accelerating": avg_acc > 0,
            "strength": (
                "RAPID" if avg_acc > 0.01 else
                "MODERATE" if avg_acc > 0.005 else
                "SLOW"
            ),
            "implication": "SHARP_MONEY_ENTERING" if avg_acc > 0.01 else "NORMAL_MOVEMENT",
        }

    def predict_odds_destination(self,
                                current_odds: float,
                                velocity: float,
                                acceleration: float,
                                time_to_match_hours: float) -> Dict:
        """
        Predice dónde estarán las odds cuando empiece el partido

        Usa: actual + (velocity × tiempo) + (aceleración × tiempo²)
        """

        # Convertir tiempo a minutos
        time_minutes = time_to_match_hours * 60

        # Predicción simple: s = s0 + v*t + 0.5*a*t²
        predicted_change = (velocity * time_minutes) + (0.5 * acceleration * (time_minutes ** 2))

        predicted_odds = current_odds + predicted_change

        return {
            "current_odds": round(current_odds, 2),
            "predicted_odds": round(predicted_odds, 2),
            "predicted_change": round(predicted_change, 2),
            "predicted_change_pct": round((predicted_change / current_odds) * 100, 2),
            "time_to_match_hours": time_to_match_hours,
            "confidence": (
                "LOW" if time_to_match_hours > 24 else
                "MEDIUM" if time_to_match_hours > 6 else
                "HIGH"
            ),
        }

    def identify_sharp_moves(self,
                            odds_timeline: List[Dict]) -> Dict:
        """
        Identifica movimientos de sharp money

        Sharp move = cambio rápido en dirección consistente
        """

        if not odds_timeline or len(odds_timeline) < 5:
            return {"error": "Need more data"}

        velocities = []

        for i in range(1, len(odds_timeline)):
            change = odds_timeline[i].get("odds") - odds_timeline[i-1].get("odds")
            time = 1  # Assuming each point is 1 unit apart
            velocities.append(change / time)

        # Detectar si todas las velocidades van en la misma dirección
        positive = sum(1 for v in velocities if v > 0)
        negative = sum(1 for v in velocities if v < 0)

        one_direction = (positive > len(velocities) * 0.7) or (negative > len(velocities) * 0.7)

        return {
            "sharp_move_detected": one_direction,
            "direction": "UP" if positive > negative else "DOWN",
            "consistency_pct": round(max(positive, negative) / len(velocities) * 100, 1),
            "strength": max(velocities) if velocities else 0,
            "implication": "FOLLOW_THE_MONEY" if one_direction else "MIXED_SIGNALS",
        }


line_velocity = LineMovementVelocity()


if __name__ == "__main__":
    print("[TEST] Line Movement Velocity\n")

    odds = [1.95, 1.98, 2.05, 2.02, 2.08]
    times = [
        datetime.now().isoformat(),
        (datetime.now() + timedelta(minutes=5)).isoformat(),
        (datetime.now() + timedelta(minutes=10)).isoformat(),
        (datetime.now() + timedelta(minutes=15)).isoformat(),
        (datetime.now() + timedelta(minutes=20)).isoformat(),
    ]

    result = line_velocity.calculate_velocity(odds, times)
    print(f"Velocity: {result['average_velocity']}")
    print(f"Intensity: {result['velocity_intensity']}")
