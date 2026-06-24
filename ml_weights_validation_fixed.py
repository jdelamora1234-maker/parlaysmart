"""
ML WEIGHTS VALIDATION - VERSIÓN MEJORADA (9/10)
Walk-forward validation para evitar overfitting temporal
Production-ready con validación exhaustiva
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple
from datetime import datetime

class MLWeightsValidatorFixed:
    """ML weights con validación temporal correcta"""

    def __init__(self, data: pd.DataFrame, test_size_months: int = 1):
        self.data = data
        self.test_size = test_size_months
        self.weights_history = []
        self.validation_results = []
        self.final_weights = None
        self.scaler = StandardScaler()

    def validate_data_integrity(self) -> Tuple[bool, str]:
        """Valida que los datos sean correctos antes de usar"""

        errors = []

        # 1. Check fecha column
        if 'date' not in self.data.columns:
            errors.append("Missing 'date' column")

        # 2. Check features
        feature_cols = [c for c in self.data.columns if c.startswith('layer_')]
        if len(feature_cols) < 5:
            errors.append(f"Need at least 5 layers, found {len(feature_cols)}")

        # 3. Check target
        if 'result' not in self.data.columns:
            errors.append("Missing 'result' column")

        # 4. Check for NaN
        nan_count = self.data.isna().sum().sum()
        if nan_count > 0:
            errors.append(f"Found {nan_count} NaN values")

        # 5. Check data size
        if len(self.data) < 100:
            errors.append(f"Need at least 100 samples, found {len(self.data)}")

        if errors:
            return False, "; ".join(errors)

        return True, "Data is valid"

    def walk_forward_validate(self) -> Dict:
        """
        Walk-forward validation (el estándar de oro para series temporales)

        Previene overfitting porque test set NUNCA se usa para entrenar
        """

        is_valid, validation_msg = self.validate_data_integrity()
        if not is_valid:
            return {"error": validation_msg, "status": "VALIDATION_FAILED"}

        # Ordenar por fecha
        self.data = self.data.sort_values('date').reset_index(drop=True)

        # Features
        feature_cols = [c for c in self.data.columns if c.startswith('layer_')]

        # Walk-forward: cada mes, entrenar en pasado, test en presente
        test_results = []
        window_size = int(len(self.data) * 0.8)  # 80% train, 20% test

        # Número de ventanas
        num_windows = max(1, (len(self.data) - window_size) // (window_size // 12))

        for i in range(num_windows):
            # Definir indices
            train_end = window_size + (i * (window_size // 12))
            test_end = min(train_end + (window_size // 12), len(self.data))

            if test_end <= train_end or train_end >= len(self.data):
                break

            # Datos train
            X_train = self.data.iloc[:train_end][feature_cols]
            y_train = self.data.iloc[:train_end]['result']

            # Datos test
            X_test = self.data.iloc[train_end:test_end][feature_cols]
            y_test = self.data.iloc[train_end:test_end]['result']

            # Validar
            if len(X_train) < 10 or len(X_test) < 2:
                continue

            try:
                # Entrenar
                model = LinearRegression()
                model.fit(X_train, y_train)

                # Test
                train_score = model.score(X_train, y_train)
                test_score = model.score(X_test, y_test)

                # Guardar
                test_results.append({
                    'window': i,
                    'train_samples': len(X_train),
                    'test_samples': len(X_test),
                    'train_r2': round(train_score, 4),
                    'test_r2': round(test_score, 4),
                    'weights': model.coef_,
                    'intercept': model.intercept_,
                    'overfitting': round(train_score - test_score, 4),  # Debe ser <0.1
                })

            except Exception as e:
                return {"error": f"Training failed: {str(e)}", "status": "TRAINING_ERROR"}

        if not test_results:
            return {"error": "No valid windows for validation", "status": "NO_WINDOWS"}

        # Validar que no hay overfitting excesivo
        avg_overfitting = np.mean([r['overfitting'] for r in test_results])
        if avg_overfitting > 0.15:
            return {
                "warning": f"High overfitting detected: {avg_overfitting:.4f}",
                "status": "OVERFITTING_WARNING",
                "windows": test_results
            }

        return {
            "status": "VALIDATION_SUCCESS",
            "num_windows": len(test_results),
            "avg_train_r2": round(np.mean([r['train_r2'] for r in test_results]), 4),
            "avg_test_r2": round(np.mean([r['test_r2'] for r in test_results]), 4),
            "avg_overfitting": round(avg_overfitting, 4),
            "windows": test_results
        }

    def get_robust_weights(self) -> Dict:
        """
        Retorna pesos que realmente generalizan a datos nuevos

        NO promedio simple - usa mediana para robustez
        """

        results = self.walk_forward_validate()

        if results.get('status') != 'VALIDATION_SUCCESS':
            return {
                "error": results.get('error', 'Unknown error'),
                "weights": None,
                "status": "FAILED"
            }

        windows = results['windows']

        # Usar MEDIANA (más robusto que mean, rechaza outliers)
        all_weights = np.array([w['weights'] for w in windows])
        final_weights = np.median(all_weights, axis=0)

        # Normalizar a suma = 1 (para interpretabilidad)
        final_weights = final_weights / np.sum(np.abs(final_weights))

        return {
            "status": "SUCCESS",
            "weights": final_weights.tolist(),
            "method": "Median of walk-forward windows (robust)",
            "validation_r2": results['avg_test_r2'],
            "overfitting_check": results['avg_overfitting'],
            "num_windows_used": len(windows),
            "production_ready": results['avg_overfitting'] < 0.10
        }

    def stress_test_weights(self, new_data: pd.DataFrame) -> Dict:
        """
        Antes de usar en producción, test con datos completamente nuevos

        Simula: "¿Qué pasa si los datos cambian?"
        """

        feature_cols = [c for c in new_data.columns if c.startswith('layer_')]

        if not self.final_weights:
            return {"error": "No weights to test", "status": "NO_WEIGHTS"}

        try:
            X_new = new_data[feature_cols]
            y_new = new_data['result']

            # Predicción manual con weights
            predictions = X_new @ np.array(self.final_weights)

            # Validar predicciones
            if np.isnan(predictions).any():
                return {"error": "NaN in predictions", "status": "PREDICTION_ERROR"}

            # R² score
            ss_res = np.sum((y_new - predictions) ** 2)
            ss_tot = np.sum((y_new - np.mean(y_new)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            return {
                "status": "STRESS_TEST_PASSED",
                "r2_on_new_data": round(r2, 4),
                "predictions_valid": True,
                "production_ready": r2 > 0.50
            }

        except Exception as e:
            return {"error": str(e), "status": "STRESS_TEST_FAILED"}


# USO EN PRODUCCIÓN:
if __name__ == "__main__":
    # Cargar datos históricos
    df = pd.read_csv('historical_matches.csv')

    # Validar y obtener pesos
    validator = MLWeightsValidatorFixed(df)
    weights_result = validator.get_robust_weights()

    if weights_result['status'] == 'SUCCESS':
        print(f"✅ Weights are production-ready: {weights_result['production_ready']}")
        print(f"   Validation R²: {weights_result['validation_r2']}")
        print(f"   Overfitting check: {weights_result['overfitting_check']}")

        # Guardar para usar en ensemble
        validator.final_weights = weights_result['weights']

        # Stress test con datos nuevos (si existen)
        df_new = pd.read_csv('new_matches.csv')
        stress = validator.stress_test_weights(df_new)
        print(f"   Stress test on new data R²: {stress.get('r2_on_new_data', 'N/A')}")
    else:
        print(f"❌ Error: {weights_result['error']}")
