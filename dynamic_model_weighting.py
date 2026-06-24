"""
DYNAMIC MODEL WEIGHTING - Pesos adaptativos para ensemble
Usa: Real-time performance tracking
Beneficio: Modelos malos automáticamente reciben menos peso
Expectativa: +5-8% mejora en predicciones
"""

import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta

class DynamicModelWeighting:
    """Ajusta pesos de modelos en ensemble basado en performance"""

    def __init__(self, models: List[str] = None):
        self.models = models or [
            "gemini_analysis",
            "elo_rating",
            "poisson_goals",
            "ml_weights",
            "market_consensus"
        ]
        self.performance_history = {m: [] for m in self.models}
        self.current_weights = {m: 0.2 for m in self.models}  # Equal initial weights
        self.weight_history = []

    def update_model_accuracy(self,
                            model_name: str,
                            prediction: float,
                            actual: float,
                            timestamp: str = None) -> Dict:
        """
        Actualiza accuracy de un modelo

        prediction: probabilidad predicha (0-1)
        actual: resultado real (0 o 1)
        """

        if timestamp is None:
            timestamp = datetime.now().isoformat()

        # Calcular error
        error = abs(prediction - actual)

        # Score: 1 - error (perfecto = 1, terrible = 0)
        score = 1 - error

        # Registrar
        self.performance_history[model_name].append({
            "timestamp": timestamp,
            "prediction": prediction,
            "actual": actual,
            "error": error,
            "score": score
        })

        return {
            "model": model_name,
            "error": round(error, 3),
            "score": round(score, 3),
            "total_predictions": len(self.performance_history[model_name]),
        }

    def calculate_model_scores(self,
                             lookback_periods: int = 50) -> Dict[str, float]:
        """
        Calcula score de cada modelo en período reciente

        Score = promedio de últimas N predicciones
        """

        scores = {}

        for model, history in self.performance_history.items():
            if not history:
                scores[model] = 0.5  # Default si no hay data
                continue

            # Últimas N predicciones
            recent = history[-lookback_periods:]

            # Promedio de scores
            avg_score = np.mean([h["score"] for h in recent])

            scores[model] = avg_score

        return scores

    def reweight_models(self,
                       lookback_periods: int = 50,
                       min_weight: float = 0.05) -> Dict:
        """
        Recalcula pesos basado en performance reciente

        Modelos mejor = peso mayor, modelos peor = peso menor
        """

        scores = self.calculate_model_scores(lookback_periods)

        # Normalizar scores a [0, 2] rango
        min_score = min(scores.values()) if scores else 0.5
        max_score = max(scores.values()) if scores else 0.5

        if max_score - min_score > 0:
            normalized = {
                m: 0.5 + 1.5 * (scores[m] - min_score) / (max_score - min_score)
                for m in self.models
            }
        else:
            normalized = {m: 1.0 for m in self.models}

        # Aplicar mínimo
        constrained = {
            m: max(normalized.get(m, 1.0), min_weight)
            for m in self.models
        }

        # Normalizar a suma = 1
        total = sum(constrained.values())
        new_weights = {m: constrained[m] / total for m in self.models}

        # Guardar cambio
        self.current_weights = new_weights
        self.weight_history.append({
            "timestamp": datetime.now().isoformat(),
            "weights": new_weights.copy(),
            "scores": scores
        })

        return {
            "new_weights": {m: round(w, 3) for m, w in new_weights.items()},
            "model_scores": {m: round(s, 3) for m, s in scores.items()},
            "weight_changes": {
                m: round(new_weights[m] - 0.2, 3) for m in self.models
            }
        }

    def detect_model_degradation(self,
                                model_name: str,
                                degradation_threshold: float = 0.1) -> Dict:
        """
        Detecta si un modelo está degradándose

        Compara últimos 20 vs anteriores 20
        """

        history = self.performance_history.get(model_name, [])

        if len(history) < 40:
            return {"error": "Not enough history", "degradation_detected": False}

        # Split
        recent = history[-20:]
        older = history[-40:-20]

        recent_avg = np.mean([h["score"] for h in recent])
        older_avg = np.mean([h["score"] for h in older])

        degradation = older_avg - recent_avg

        return {
            "model": model_name,
            "older_avg_score": round(older_avg, 3),
            "recent_avg_score": round(recent_avg, 3),
            "degradation": round(degradation, 3),
            "degradation_pct": round(degradation / max(older_avg, 0.1) * 100, 1),
            "degradation_detected": degradation > degradation_threshold,
            "action": (
                "REDUCE_WEIGHT_SIGNIFICANTLY" if degradation > 0.15 else
                "REDUCE_WEIGHT" if degradation_detected else
                "MONITOR"
            )
        }

    def ensemble_prediction_with_dynamic_weights(self,
                                                predictions: Dict[str, float]) -> Dict:
        """
        Combina predicciones usando pesos dinámicos

        predictions: {"gemini_analysis": 0.65, "elo_rating": 0.60, ...}
        """

        weighted_sum = 0
        total_weight = 0

        for model, prediction in predictions.items():
            weight = self.current_weights.get(model, 0.2)
            weighted_sum += prediction * weight
            total_weight += weight

        ensemble = weighted_sum / total_weight if total_weight > 0 else 0.5

        return {
            "individual_predictions": predictions,
            "weights_used": {m: round(w, 3) for m, w in self.current_weights.items()},
            "ensemble_prediction": round(ensemble, 3),
            "confidence": round(max(predictions.values()) - min(predictions.values()), 3),
            "weight_concentration": round(max(self.current_weights.values()), 3),
        }

    def get_weighting_report(self) -> Dict:
        """Reporte completo de pesos y performance"""

        scores = self.calculate_model_scores()

        return {
            "current_weights": {m: round(w, 3) for m, w in self.current_weights.items()},
            "model_scores": {m: round(s, 3) for m, s in scores.items()},
            "best_model": max(scores, key=scores.get),
            "worst_model": min(scores, key=scores.get),
            "weight_history_length": len(self.weight_history),
            "last_reweight": self.weight_history[-1] if self.weight_history else None,
        }


dynamic_weighting = DynamicModelWeighting()


if __name__ == "__main__":
    print("[TEST] Dynamic Model Weighting\n")

    # Simular predicciones
    updates = [
        ("gemini_analysis", 0.70, 1),
        ("elo_rating", 0.60, 1),
        ("poisson_goals", 0.65, 1),
        ("ml_weights", 0.72, 1),
        ("market_consensus", 0.68, 1),
    ]

    for model, pred, actual in updates:
        dynamic_weighting.update_model_accuracy(model, pred, actual)

    # Reweight
    result = dynamic_weighting.reweight_models()
    print(f"New weights: {result['new_weights']}\n")

    # Ensemble
    new_preds = {
        "gemini_analysis": 0.70,
        "elo_rating": 0.60,
        "poisson_goals": 0.65,
        "ml_weights": 0.72,
        "market_consensus": 0.68,
    }

    ensemble = dynamic_weighting.ensemble_prediction_with_dynamic_weights(new_preds)
    print(f"Ensemble: {ensemble['ensemble_prediction']}")
