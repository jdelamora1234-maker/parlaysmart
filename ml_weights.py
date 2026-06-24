"""
ML WEIGHTS - Ajuste Automático de Pesos de Capas
Sistema aprende qué capas predicen mejor/peor
Después de 20+ análisis: pesos optimales
Entrada: [Capa1, Capa2, ..., Capa30] + Resultado Real
Salida: Pesos ajustados automáticamente
"""

import numpy as np
import json
from typing import Dict, List
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

class LayerWeightOptimizer:
    """
    Aprende combinación óptima de 30 capas
    Usa regresión lineal para predecir resultado
    Ajusta pesos automáticamente
    """

    def __init__(self):
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.layer_weights = self._init_default_weights()
        self.training_data = []
        self.training_targets = []

    def _init_default_weights(self) -> Dict[int, float]:
        """Pesos iniciales (iguales para todas las capas)"""
        return {i: 1.0 / 30 for i in range(1, 31)}

    def add_training_sample(self,
                           layer_features: Dict[int, float],
                           actual_result: int):
        """
        Agrega muestra de entrenamiento
        layer_features: {1: valor, 2: valor, ..., 30: valor}
        actual_result: 1 (ganó) o 0 (perdió)
        """

        # Convertir dict a vector
        features = [layer_features.get(i, 0) for i in range(1, 31)]
        self.training_data.append(features)
        self.training_targets.append(actual_result)

    def train(self):
        """Entrena modelo con datos acumulados"""

        if len(self.training_data) < 10:
            print(f"[ML_WEIGHTS] ⚠️ Insuficientes muestras (need ≥10, have {len(self.training_data)})")
            return False

        # Normalizar datos
        X = np.array(self.training_data)
        y = np.array(self.training_targets)

        X_scaled = self.scaler.fit_transform(X)

        # Entrenar regresión
        self.model.fit(X_scaled, y)

        # Actualizar pesos basados en coeficientes
        coefficients = self.model.coef_
        coefficients_normalized = np.abs(coefficients) / np.sum(np.abs(coefficients))

        for i in range(1, 31):
            self.layer_weights[i] = float(coefficients_normalized[i - 1])

        score = self.model.score(X_scaled, y)
        print(f"[ML_WEIGHTS] ✅ Modelo entrenado. Score: {score:.3f}")
        print(f"[ML_WEIGHTS] Top 5 capas:")

        top_layers = sorted(self.layer_weights.items(), key=lambda x: x[1], reverse=True)[:5]
        for capa, peso in top_layers:
            print(f"  Capa {capa}: {peso:.3f}")

        return True

    def get_optimized_weights(self) -> Dict[int, float]:
        """Retorna pesos optimizados"""
        return self.layer_weights.copy()

    def predict_with_optimized(self, layer_features: Dict[int, float]) -> float:
        """Predice usando pesos optimizados"""

        # Convertir a vector
        features = np.array([layer_features.get(i, 0) for i in range(1, 31)]).reshape(1, -1)

        # Normalizar con el scaler de entrenamiento
        try:
            features_scaled = self.scaler.transform(features)
            prediction = self.model.predict(features_scaled)[0]
            return float(np.clip(prediction, 0, 1))  # Clip a [0, 1]
        except:
            # Fallback si no hay modelo entrenado
            return 0.5

    def layer_importance(self) -> Dict[int, float]:
        """Retorna importancia de cada capa (correlación con resultado)"""

        if len(self.training_data) < 5:
            return {}

        X = np.array(self.training_data)
        y = np.array(self.training_targets)

        correlations = {}
        for i in range(30):
            if np.std(X[:, i]) > 0:
                corr = np.corrcoef(X[:, i], y)[0, 1]
                correlations[i + 1] = float(corr) if not np.isnan(corr) else 0

        return correlations

    def diagnose_weak_layers(self) -> List[int]:
        """Identifica capas que predicen PEOR"""

        importance = self.layer_importance()
        if not importance:
            return []

        # Capas con correlación negativa o muy baja
        weak = [capa for capa, corr in importance.items() if corr < 0.1]
        return weak

    def diagnose_strong_layers(self) -> List[int]:
        """Identifica capas que predicen MEJOR"""

        importance = self.layer_importance()
        if not importance:
            return []

        # Capas con correlación positiva alta
        strong = [capa for capa, corr in importance.items() if corr > 0.4]
        return strong

    def export_weights_json(self, filepath: str):
        """Exporta pesos a archivo JSON"""

        data = {
            "timestamp": str(np.datetime64('now')),
            "model_score": float(self.model.score(
                self.scaler.transform(np.array(self.training_data)),
                np.array(self.training_targets)
            )) if len(self.training_data) > 0 else 0,
            "weights": self.layer_weights,
            "strong_layers": self.diagnose_strong_layers(),
            "weak_layers": self.diagnose_weak_layers(),
            "samples_trained": len(self.training_data),
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"[ML_WEIGHTS] ✅ Pesos exportados a {filepath}")


class LayerWeightValidator:
    """
    Valida que los pesos sean razonables
    Evita overfitting
    Verifica cross-validation
    """

    @staticmethod
    def cross_validation_score(optimizer: LayerWeightOptimizer, k: int = 5) -> float:
        """Calcula cross-validation score (k-fold)"""

        if len(optimizer.training_data) < k:
            return 0

        X = np.array(optimizer.training_data)
        y = np.array(optimizer.training_targets)

        fold_size = len(X) // k
        scores = []

        for i in range(k):
            # Split train/test
            test_idx = slice(i * fold_size, (i + 1) * fold_size)
            train_idx = list(range(i * fold_size)) + list(range((i + 1) * fold_size, len(X)))

            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            # Entrenar
            model = LinearRegression()
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            model.fit(X_train_scaled, y_train)

            # Evaluar
            X_test_scaled = scaler.transform(X_test)
            score = model.score(X_test_scaled, y_test)
            scores.append(score)

        avg_score = np.mean(scores)
        print(f"[VALIDATION] Cross-Validation Score (k={k}): {avg_score:.3f}")
        return avg_score

    @staticmethod
    def detect_overfitting(optimizer: LayerWeightOptimizer, cv_threshold: float = 0.7) -> bool:
        """Detecta si hay overfitting"""

        if len(optimizer.training_data) < 20:
            return False

        # Score en datos de entrenamiento
        train_score = optimizer.model.score(
            optimizer.scaler.transform(np.array(optimizer.training_data)),
            np.array(optimizer.training_targets)
        )

        # Score en cross-validation
        cv_score = LayerWeightValidator.cross_validation_score(optimizer)

        # Si diferencia es grande = overfitting
        if train_score - cv_score > 0.2:
            print(f"[OVERFITTING] ⚠️ Detección: Train={train_score:.3f}, CV={cv_score:.3f}")
            return True

        return False


# SINGLETON GLOBAL
optimizer = LayerWeightOptimizer()
validator = LayerWeightValidator()


if __name__ == "__main__":
    print("[TEST] Simulando entrenamiento con 20 muestras...")

    # Simular 20 análisis
    np.random.seed(42)
    for i in range(20):
        layer_features = {j: np.random.random() for j in range(1, 31)}
        actual_result = np.random.randint(0, 2)
        optimizer.add_training_sample(layer_features, actual_result)

    print("\n[TEST] Entrenando modelo...")
    optimizer.train()

    print("\n[TEST] Validación cruzada...")
    validator.cross_validation_score(optimizer, k=5)

    print("\n[TEST] Detectando overfitting...")
    validator.detect_overfitting(optimizer)

    print("\n[TEST] Capas fuertes:")
    strong = optimizer.diagnose_strong_layers()
    print(f"  {strong}")

    print("\n[TEST] Capas débiles:")
    weak = optimizer.diagnose_weak_layers()
    print(f"  {weak}")

    print("\n[TEST] Exportando pesos...")
    optimizer.export_weights_json("weights_optimized.json")
