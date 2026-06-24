"""
BACKTEST - Validación Histórica
Re-analiza últimos 50 partidos
Compara: "¿Qué hubiera predicho hace 50 partidos?"
Vs: Resultado real
Responde: "¿El sistema realmente funciona o es suerte?"
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List
from tracking import tracker

class Backtester:
    """
    Ejecuta análisis históricos
    Valida precisión real
    Identifica patrones de error
    """

    def __init__(self, lookback_days: int = 180):
        self.lookback_days = lookback_days
        self.results = []

    def run_backtest(self, matches_data: List[Dict]):
        """
        Ejecuta backtest en histórico
        matches_data: Lista de {team_a, team_b, date, actual_result}
        """

        print(f"[BACKTEST] Ejecutando backtest de {len(matches_data)} partidos...")

        stats = {
            "total": len(matches_data),
            "ultra_wins": 0,
            "ultra_total": 0,
            "conservador_wins": 0,
            "conservador_total": 0,
            "balanceado_wins": 0,
            "balanceado_total": 0,
            "riesgoso_wins": 0,
            "riesgoso_total": 0,
            "details": []
        }

        for match in matches_data:
            match_id = f"{match['team_a']}-{match['team_b']}-{match['date']}"

            # Simulación: obtener análisis guardado o re-analizar
            result = self._backtest_match(match, match_id)

            if result:
                stats["details"].append(result)

                # Contar wins
                if result["ultra_win"]:
                    stats["ultra_wins"] += 1
                stats["ultra_total"] += 1

                if result["conservador_win"]:
                    stats["conservador_wins"] += 1
                stats["conservador_total"] += 1

                if result["balanceado_win"]:
                    stats["balanceado_wins"] += 1
                stats["balanceado_total"] += 1

                if result["riesgoso_win"]:
                    stats["riesgoso_wins"] += 1
                stats["riesgoso_total"] += 1

        # Calcular hit rates
        self._calculate_hit_rates(stats)
        self.results = stats

        return stats

    def _backtest_match(self, match: Dict, match_id: str) -> Dict:
        """Backtest de un partido individual"""

        try:
            # Simulación: obtener análisis de base de datos
            # En realidad, llamarías al modelo histórico
            prediction = {
                "home_win": 0.62,
                "draw": 0.24,
                "away_win": 0.14,
            }

            # Determinar ganador predicho
            predicted_winner = max(prediction, key=prediction.get)

            # Obtener resultado real
            actual_result = match.get("actual_result", "unknown")

            # Evaluar cada parlay
            ultra_win = self._check_parlay(
                predicted=predicted_winner,
                actual=actual_result,
                parlay_type="ultra"
            )

            conservador_win = self._check_parlay(
                predicted=predicted_winner,
                actual=actual_result,
                parlay_type="conservador"
            )

            balanceado_win = self._check_parlay(
                predicted=predicted_winner,
                actual=actual_result,
                parlay_type="balanceado"
            )

            riesgoso_win = self._check_parlay(
                predicted=predicted_winner,
                actual=actual_result,
                parlay_type="riesgoso"
            )

            return {
                "match_id": match_id,
                "date": match.get("date"),
                "team_a": match.get("team_a"),
                "team_b": match.get("team_b"),
                "predicted": predicted_winner,
                "actual": actual_result,
                "ultra_win": ultra_win,
                "conservador_win": conservador_win,
                "balanceado_win": balanceado_win,
                "riesgoso_win": riesgoso_win,
            }

        except Exception as e:
            print(f"[BACKTEST] Error en {match_id}: {e}")
            return None

    def _check_parlay(self, predicted: str, actual: str, parlay_type: str) -> bool:
        """
        Verifica si un parlay hubiera ganado
        SIMPLIFICADO: solo chequea si el ganador predicho coincide
        TODO: Expandir para validar TODOS los picks
        """

        if parlay_type == "ultra":
            # Ultra conservador: solo gana si ganador predicho es correcto
            return predicted == actual

        elif parlay_type == "conservador":
            # Conservador: gana si ganador predicho es correcto
            return predicted == actual

        elif parlay_type == "balanceado":
            # Balanceado: gana si predicción está en rango aceptable
            # Simulación: 60% de probabilidad si está dentro de 1 gol esperado
            return predicted == actual

        elif parlay_type == "riesgoso":
            # Riesgoso: gana solo si es predicción perfecta (más estricto)
            return predicted == actual

        return False

    def _calculate_hit_rates(self, stats: Dict):
        """Calcula hit rates finales"""

        if stats["ultra_total"] > 0:
            stats["ultra_hit_rate"] = stats["ultra_wins"] / stats["ultra_total"]
        if stats["conservador_total"] > 0:
            stats["conservador_hit_rate"] = stats["conservador_wins"] / stats["conservador_total"]
        if stats["balanceado_total"] > 0:
            stats["balanceado_hit_rate"] = stats["balanceado_wins"] / stats["balanceado_total"]
        if stats["riesgoso_total"] > 0:
            stats["riesgoso_hit_rate"] = stats["riesgoso_wins"] / stats["riesgoso_total"]

    def get_results(self) -> Dict:
        """Retorna resultados del backtest"""
        return self.results

    def print_report(self):
        """Imprime reporte formateado"""

        if not self.results:
            print("[BACKTEST] Sin resultados")
            return

        print("\n" + "=" * 80)
        print("BACKTEST REPORT")
        print("=" * 80)

        print(f"\nTotal partidos: {self.results['total']}")

        print("\n📊 RESULTADOS POR TIPO DE PARLAY:")
        print(f"  Ultra Conservador:    {self.results.get('ultra_wins', 0)}/{self.results.get('ultra_total', 0)} ({self.results.get('ultra_hit_rate', 0)*100:.1f}%)")
        print(f"  Conservador:          {self.results.get('conservador_wins', 0)}/{self.results.get('conservador_total', 0)} ({self.results.get('conservador_hit_rate', 0)*100:.1f}%)")
        print(f"  Balanceado:           {self.results.get('balanceado_wins', 0)}/{self.results.get('balanceado_total', 0)} ({self.results.get('balanceado_hit_rate', 0)*100:.1f}%)")
        print(f"  Riesgoso:             {self.results.get('riesgoso_wins', 0)}/{self.results.get('riesgoso_total', 0)} ({self.results.get('riesgoso_hit_rate', 0)*100:.1f}%)")

        print("\n🎯 VEREDICTO:")
        overall = (
            self.results.get('ultra_hit_rate', 0) +
            self.results.get('conservador_hit_rate', 0) +
            self.results.get('balanceado_hit_rate', 0) +
            self.results.get('riesgoso_hit_rate', 0)
        ) / 4

        if overall > 0.55:
            print(f"  ✅ Sistema VÁLIDO (Hit rate promedio: {overall*100:.1f}%)")
        elif overall > 0.50:
            print(f"  ⚠️  Sistema MARGINAL (Hit rate promedio: {overall*100:.1f}%)")
        else:
            print(f"  ❌ Sistema FALLIDO (Hit rate promedio: {overall*100:.1f}%)")

        print("\n💡 RECOMENDACIONES:")
        if self.results.get('ultra_hit_rate', 0) > 0.60:
            print("  - Ultra Conservador: ✅ Funciona bien, usar en vivo")
        if self.results.get('conservador_hit_rate', 0) > 0.55:
            print("  - Conservador: ✅ Funciona, usar como base")
        if self.results.get('balanceado_hit_rate', 0) > 0.45:
            print("  - Balanceado: ⚠️  Mediocre, ajustar estrategia")
        if self.results.get('riesgoso_hit_rate', 0) > 0.20:
            print("  - Riesgoso: ✅ Excelente ROI si acumula")

        print("\n" + "=" * 80)

    def export_backtest_json(self, filepath: str):
        """Exporta resultados a JSON"""

        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"[BACKTEST] ✅ Resultados exportados a {filepath}")


# SINGLETON GLOBAL
backtester = Backtester()


if __name__ == "__main__":
    print("[TEST] Ejecutando backtest simulado con 50 partidos...")

    # Simular 50 partidos históricos
    import random
    matches_data = []
    for i in range(50):
        matches_data.append({
            "team_a": f"Team A",
            "team_b": f"Team B",
            "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
            "actual_result": random.choice(["home", "draw", "away"])
        })

    results = backtester.run_backtest(matches_data)

    print("\n[TEST] Imprimiendo reporte...")
    backtester.print_report()

    print("\n[TEST] Exportando JSON...")
    backtester.export_backtest_json("backtest_results.json")
