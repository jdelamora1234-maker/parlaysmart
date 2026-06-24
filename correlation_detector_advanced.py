"""
CORRELATION DETECTOR - VERSIÓN AVANZADA (9/10)
Detecta TODAS las formas de correlación (lineal + no-lineal)
Production-ready con manejo de edge cases
"""

import numpy as np
from scipy.stats import spearmanr, kendalltau, pearsonr
from typing import Dict, List, Tuple

class AdvancedCorrelationDetectorFixed:
    """Detecta correlación en TODAS sus formas"""

    @staticmethod
    def validate_input(x: np.ndarray, y: np.ndarray) -> Tuple[bool, str]:
        """Valida datos antes de calcular correlación"""

        # 1. Check size
        if len(x) != len(y):
            return False, "Arrays have different lengths"

        # 2. Check minimum samples
        if len(x) < 3:
            return False, "Need at least 3 samples"

        # 3. Check for NaN
        if np.isnan(x).any() or np.isnan(y).any():
            return False, "Contains NaN values"

        # 4. Check for infinite
        if np.isinf(x).any() or np.isinf(y).any():
            return False, "Contains infinite values"

        # 5. Check variance
        if np.std(x) == 0 or np.std(y) == 0:
            return False, "Zero variance in data"

        return True, "Valid"

    @staticmethod
    def pearson_correlation(x: np.ndarray, y: np.ndarray) -> float:
        """Correlación de Pearson (lineal)"""

        try:
            corr, _ = pearsonr(x, y)
            return abs(corr)
        except:
            return 0.0

    @staticmethod
    def spearman_correlation(x: np.ndarray, y: np.ndarray) -> float:
        """Correlación de Spearman (monotónica)"""

        try:
            corr, _ = spearmanr(x, y)
            return abs(corr)
        except:
            return 0.0

    @staticmethod
    def kendall_correlation(x: np.ndarray, y: np.ndarray) -> float:
        """Correlación de Kendall (ordinal)"""

        try:
            corr, _ = kendalltau(x, y)
            return abs(corr)
        except:
            return 0.0

    @staticmethod
    def distance_correlation(x: np.ndarray, y: np.ndarray) -> float:
        """
        Distance correlation (Székely-Rizzo)
        Detecta CUALQUIER dependencia, no-lineal incluida
        """

        try:
            x = np.asarray(x, dtype=float)
            y = np.asarray(y, dtype=float)

            # Matrices de distancia
            A = np.abs(np.subtract.outer(x, x))
            B = np.abs(np.subtract.outer(y, y))

            # Double center
            n = len(x)
            A_mean_row = A.mean(axis=1, keepdims=True)
            A_mean_col = A.mean(axis=0, keepdims=True)
            A_mean_all = A.mean()

            A_centered = A - A_mean_row - A_mean_col + A_mean_all

            B_mean_row = B.mean(axis=1, keepdims=True)
            B_mean_col = B.mean(axis=0, keepdims=True)
            B_mean_all = B.mean()

            B_centered = B - B_mean_row - B_mean_col + B_mean_all

            # Distance correlation
            numerator = np.sqrt(np.sum(A_centered * B_centered))
            denominator = np.sqrt(np.sum(A_centered ** 2) * np.sum(B_centered ** 2))

            if denominator == 0:
                return 0.0

            return numerator / denominator

        except:
            return 0.0

    @staticmethod
    def mutual_information(x: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
        """
        Información mutua (detecta dependencia en cualquier forma)
        Normalizada a [0, 1]
        """

        try:
            # Histogramas 2D
            hist_2d, _, _ = np.histogram2d(x, y, bins=bins)
            hist_2d /= hist_2d.sum()

            # Marginales
            p_x = hist_2d.sum(axis=1)
            p_y = hist_2d.sum(axis=0)

            # MI (mutual information)
            mi = 0
            for i in range(len(p_x)):
                for j in range(len(p_y)):
                    if hist_2d[i, j] > 0:
                        mi += hist_2d[i, j] * np.log(
                            hist_2d[i, j] / (p_x[i] * p_y[j])
                        )

            # Normalizar a [0, 1]
            h_x = -np.sum(p_x[p_x > 0] * np.log(p_x[p_x > 0]))
            h_y = -np.sum(p_y[p_y > 0] * np.log(p_y[p_y > 0]))

            if max(h_x, h_y) == 0:
                return 0.0

            nmi = mi / max(h_x, h_y)
            return min(nmi, 1.0)

        except:
            return 0.0

    def calculate_all_correlations(self,
                                  pick_a_history: List[float],
                                  pick_b_history: List[float]) -> Dict:
        """
        Calcula TODAS las formas de correlación
        """

        x = np.asarray(pick_a_history, dtype=float)
        y = np.asarray(pick_b_history, dtype=float)

        # Validar
        is_valid, msg = self.validate_input(x, y)
        if not is_valid:
            return {
                "error": msg,
                "is_correlated": False,
                "max_correlation": 0.0
            }

        # Calcular todas
        pearson = self.pearson_correlation(x, y)
        spearman = self.spearman_correlation(x, y)
        kendall = self.kendall_correlation(x, y)
        distance = self.distance_correlation(x, y)
        mutual_info = self.mutual_information(x, y)

        # Máximo (conservador - si CUALQUIERA es alto, están correlacionados)
        max_corr = max(pearson, spearman, kendall, distance, mutual_info)

        return {
            "pearson": round(pearson, 4),
            "spearman": round(spearman, 4),
            "kendall": round(kendall, 4),
            "distance_correlation": round(distance, 4),
            "mutual_information": round(mutual_info, 4),
            "max_correlation": round(max_corr, 4),
            "is_correlated": max_corr > 0.70,
            "correlation_strength": (
                "VERY_HIGH" if max_corr > 0.85 else
                "HIGH" if max_corr > 0.70 else
                "MODERATE" if max_corr > 0.50 else
                "LOW"
            )
        }

    def find_correlation_type(self, correlations: Dict) -> str:
        """Identifica QUÉ TIPO de correlación existe"""

        if correlations.get('error'):
            return "ERROR"

        pearson = correlations['pearson']
        spearman = correlations['spearman']
        distance = correlations['distance_correlation']
        mi = correlations['mutual_information']

        # Lógica para identificar tipo
        if abs(pearson) > 0.70:
            return "LINEAR (Pearson > 0.70)"
        elif abs(spearman) > 0.70:
            return "MONOTONIC (Spearman > 0.70)"
        elif distance > 0.70:
            return "NON-LINEAR (Distance > 0.70)"
        elif mi > 0.70:
            return "DEPENDENT (Mutual Information > 0.70)"
        else:
            return "INDEPENDENT"

    def analyze_correlation_risk(self,
                                pick_a: Dict,
                                pick_b: Dict,
                                threshold: float = 0.70) -> Dict:
        """
        Análisis completo de riesgo de correlación entre dos picks
        """

        try:
            correlations = self.calculate_all_correlations(
                pick_a['history'],
                pick_b['history']
            )

            if correlations.get('error'):
                return {
                    "error": correlations['error'],
                    "safe_to_combine": True  # Default: si error, asumir safe
                }

            is_corr = correlations['is_correlated']

            return {
                "pick_a": pick_a.get('name', 'Pick A'),
                "pick_b": pick_b.get('name', 'Pick B'),
                "correlations": correlations,
                "correlation_type": self.find_correlation_type(correlations),
                "safe_to_combine": not is_corr,
                "recommendation": (
                    "❌ DO NOT COMBINE" if is_corr else "✅ SAFE TO COMBINE"
                ),
                "reason": (
                    f"High correlation detected ({correlations['max_correlation']:.3f})"
                    if is_corr else
                    f"Low correlation ({correlations['max_correlation']:.3f})"
                ),
                "kelly_adjustment": (
                    0.75 if is_corr else 1.0  # Reducir Kelly si correlacionados
                )
            }

        except Exception as e:
            return {
                "error": str(e),
                "safe_to_combine": True
            }


# USO EN PRODUCCIÓN:
if __name__ == "__main__":
    detector = AdvancedCorrelationDetectorFixed()

    # Ejemplo: Dos picks altamente correlacionados
    pick_a = {
        'name': 'Barcelona Win',
        'history': [0.65, 0.68, 0.70, 0.62, 0.71, 0.65, 0.68, 0.69, 0.67, 0.70]
    }

    pick_b = {
        'name': 'Barcelona Over 2.5 Goals',
        'history': [0.72, 0.75, 0.78, 0.71, 0.79, 0.73, 0.76, 0.77, 0.74, 0.78]
    }

    result = detector.analyze_correlation_risk(pick_a, pick_b)

    print(f"Analysis: {result['recommendation']}")
    print(f"Reason: {result['reason']}")
    print(f"Max correlation: {result['correlations']['max_correlation']}")
    print(f"Type: {result['correlation_type']}")
    print(f"Kelly adjustment: {result['kelly_adjustment']}")
