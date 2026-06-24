"""
ENSEMBLE PREDICTOR v2.4 - Combina múltiples modelos para máxima precisión
Combina: Gemini + Elo + Poisson + ML + Market = Predicción optimal
Objetivo: Reducir error de predicción individual, mejorar a 70%+ hit rate
"""

import numpy as np
from typing import Dict, Tuple, List

class EnsemblePredictor:
    """Combina múltiples predictores con pesos óptimos"""

    def __init__(self):
        # Pesos iniciales - serán optimizados por ML
        self.weights = {
            "gemini_analysis": 0.35,      # Análisis 30 capas
            "elo_rating": 0.20,           # Sistema ELO histórico
            "poisson_model": 0.20,        # Distribución de Poisson
            "ml_model": 0.15,             # ML weights optimizados
            "market_consensus": 0.10,     # Consenso de mercado
        }

    def predict_match_outcome(self,
                            gemini_prob: float,
                            elo_home: float,
                            elo_away: float,
                            poisson_probs: Dict[str, float],
                            ml_score: float,
                            market_odds: Dict[str, float]) -> Dict[str, float]:
        """
        ENSEMBLE: Combina 5 predictores

        gemini_prob: Probabilidad según Gemini 30 capas (0-1)
        elo_home, elo_away: Ratings ELO
        poisson_probs: {"home": 0.55, "draw": 0.25, "away": 0.20}
        ml_score: Score ML (0-1)
        market_odds: {"home": 1.95, "draw": 3.20, "away": 3.50}
        """

        # 1. GEMINI ANALYSIS (35%)
        gemini_home = gemini_prob
        gemini_draw = 0.25  # Simulado
        gemini_away = 1 - gemini_home - gemini_draw

        # 2. ELO RATING (20%)
        elo_diff = elo_home - elo_away
        elo_home_prob = 1 / (1 + 10 ** (-elo_diff / 400))  # ELO probability formula
        elo_draw = 0.25  # ELO tiene sesgo
        elo_away_prob = 1 - elo_home_prob - elo_draw

        # 3. POISSON MODEL (20%)
        poisson_home = poisson_probs.get("home", 0.45)
        poisson_draw = poisson_probs.get("draw", 0.30)
        poisson_away = poisson_probs.get("away", 0.25)

        # 4. ML MODEL (15%)
        # ml_score es 0-1, convertir a probabilidades
        ml_home = 0.5 + (ml_score - 0.5) * 0.5  # Modular para evitar extremos
        ml_draw = 0.25
        ml_away = 1 - ml_home - ml_draw

        # 5. MARKET CONSENSUS (10%)
        market_home = 1 / market_odds["home"] if market_odds["home"] > 0 else 0.45
        market_draw = 1 / market_odds["draw"] if market_odds["draw"] > 0 else 0.25
        market_away = 1 / market_odds["away"] if market_odds["away"] > 0 else 0.30

        # Normalizar market
        market_sum = market_home + market_draw + market_away
        market_home /= market_sum
        market_draw /= market_sum
        market_away /= market_sum

        # ENSEMBLE: Weighted average
        ensemble_home = (
            self.weights["gemini_analysis"] * gemini_home +
            self.weights["elo_rating"] * elo_home_prob +
            self.weights["poisson_model"] * poisson_home +
            self.weights["ml_model"] * ml_home +
            self.weights["market_consensus"] * market_home
        )

        ensemble_draw = (
            self.weights["gemini_analysis"] * gemini_draw +
            self.weights["elo_rating"] * elo_draw +
            self.weights["poisson_model"] * poisson_draw +
            self.weights["ml_model"] * ml_draw +
            self.weights["market_consensus"] * market_draw
        )

        ensemble_away = (
            self.weights["gemini_analysis"] * gemini_away +
            self.weights["elo_rating"] * elo_away_prob +
            self.weights["poisson_model"] * poisson_away +
            self.weights["ml_model"] * ml_away +
            self.weights["market_consensus"] * market_away
        )

        # Normalizar
        total = ensemble_home + ensemble_draw + ensemble_away
        ensemble_home /= total
        ensemble_draw /= total
        ensemble_away /= total

        return {
            "home": round(ensemble_home, 3),
            "draw": round(ensemble_draw, 3),
            "away": round(ensemble_away, 3),
            "confidence": round(max(ensemble_home, ensemble_draw, ensemble_away), 3),
        }

    def predict_score(self,
                     lambda_home: float,
                     lambda_away: float) -> Tuple[float, float]:
        """
        Predice score esperado usando Poisson
        """
        # Usar lambdas directamente (ya calculados)
        return round(lambda_home, 2), round(lambda_away, 2)

    def calculate_ensemble_confidence(self,
                                     predictions: List[Tuple[str, float]]) -> float:
        """
        Calcula confianza del ensemble basado en acuerdo entre modelos

        predictions: [("gemini", 0.62), ("elo", 0.58), ("poisson", 0.60), ...]
        """

        if not predictions:
            return 0.5

        # Calcular desviación estándar
        probs = [p[1] for p in predictions]
        mean_prob = np.mean(probs)
        std_prob = np.std(probs)

        # Confianza = inverso de variación
        # Si todos los modelos están de acuerdo: std = 0, confianza = 1.0
        # Si están dispersos: std = 0.2, confianza = 0.5
        confidence = 1.0 - (std_prob * 2)  # Escalar para sensibilidad
        confidence = max(0.0, min(1.0, confidence))

        return round(confidence, 3)

    def optimize_weights(self, historical_predictions: List[Dict], actual_results: List[str]):
        """
        Optimiza pesos del ensemble usando histórico

        historical_predictions: [{"gemini": 0.62, "elo": 0.58, ...}, ...]
        actual_results: ["home", "draw", "away", ...]
        """

        # Algoritmo simple: ajustar pesos para maximizar accuracy
        best_weights = self.weights.copy()
        best_accuracy = 0

        # Grid search sobre combinaciones de pesos
        for gemini_w in np.arange(0.2, 0.5, 0.05):
            for elo_w in np.arange(0.1, 0.3, 0.05):
                for poisson_w in np.arange(0.1, 0.3, 0.05):
                    for ml_w in np.arange(0.05, 0.25, 0.05):
                        market_w = 1.0 - (gemini_w + elo_w + poisson_w + ml_w)

                        if market_w < 0 or market_w > 0.2:
                            continue

                        # Test estas pesas
                        correct = 0
                        for pred, actual in zip(historical_predictions, actual_results):
                            ensemble_prob = (
                                gemini_w * pred.get("gemini", 0.5) +
                                elo_w * pred.get("elo", 0.5) +
                                poisson_w * pred.get("poisson", 0.5) +
                                ml_w * pred.get("ml", 0.5) +
                                market_w * pred.get("market", 0.5)
                            )

                            # Predicción
                            if ensemble_prob > 0.5 and actual == "home":
                                correct += 1
                            elif ensemble_prob < 0.5 and actual == "away":
                                correct += 1

                        accuracy = correct / len(historical_predictions)

                        if accuracy > best_accuracy:
                            best_accuracy = accuracy
                            best_weights = {
                                "gemini_analysis": gemini_w,
                                "elo_rating": elo_w,
                                "poisson_model": poisson_w,
                                "ml_model": ml_w,
                                "market_consensus": market_w,
                            }

        self.weights = best_weights
        return best_accuracy


# Singleton
ensemble = EnsemblePredictor()


if __name__ == "__main__":
    print("[TEST] Ensemble Predictor v2.4\n")

    # Test
    prediction = ensemble.predict_match_outcome(
        gemini_prob=0.62,
        elo_home=1650,
        elo_away=1620,
        poisson_probs={"home": 0.55, "draw": 0.25, "away": 0.20},
        ml_score=0.58,
        market_odds={"home": 1.95, "draw": 3.20, "away": 3.50}
    )

    print("ENSEMBLE PREDICTION:")
    print(f"  Home: {prediction['home']*100:.1f}%")
    print(f"  Draw: {prediction['draw']*100:.1f}%")
    print(f"  Away: {prediction['away']*100:.1f}%")
    print(f"  Confidence: {prediction['confidence']*100:.1f}%")

    # Confidence test
    predictions = [
        ("Gemini", 0.62),
        ("ELO", 0.58),
        ("Poisson", 0.60),
        ("ML", 0.59),
        ("Market", 0.61),
    ]

    confidence = ensemble.calculate_ensemble_confidence(predictions)
    print(f"\nEnsemble confidence: {confidence*100:.1f}%")
    print("(Basado en acuerdo entre modelos)")
