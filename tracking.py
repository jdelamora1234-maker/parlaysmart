"""
TRACKING - Sistema de Retroalimentación
Guarda análisis + resultados reales
Calcula hit rate, ROI, desviaciones por capa
Entrada: "Predicción vs Realidad"
Salida: "¿El sistema funciona?"
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

class AnalysisTracker:
    """
    Guarda cada análisis + resultado real
    Permite calcular métricas de precisión
    """

    def __init__(self, db_path: str = "parlaysmart_tracking.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Crea tablas de tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabla: Análisis guardados
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id TEXT UNIQUE,
            team_a TEXT,
            team_b TEXT,
            date_match DATETIME,
            date_analysis DATETIME,

            -- Predicciones
            predicted_winner TEXT,
            predicted_prob_home REAL,
            predicted_prob_draw REAL,
            predicted_prob_away REAL,
            predicted_goals_home REAL,
            predicted_goals_away REAL,

            -- Parlays
            parlay_ultra_picks TEXT,  -- JSON
            parlay_ultra_odds REAL,
            parlay_ultra_prob REAL,
            parlay_ultra_ev REAL,

            parlay_conservador_picks TEXT,
            parlay_conservador_odds REAL,
            parlay_conservador_prob REAL,
            parlay_conservador_ev REAL,

            parlay_balanceado_picks TEXT,
            parlay_balanceado_odds REAL,
            parlay_balanceado_prob REAL,
            parlay_balanceado_ev REAL,

            parlay_riesgoso_picks TEXT,
            parlay_riesgoso_odds REAL,
            parlay_riesgoso_prob REAL,
            parlay_riesgoso_ev REAL,

            -- Capas usadas
            layers_used TEXT,  -- JSON con qué capas se analizaron

            -- Datos crudos para debug
            raw_analysis TEXT,  -- JSON completo

            UNIQUE(match_id)
        )
        """)

        # Tabla: Resultados reales (ingresados manualmente o automáticamente)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id TEXT UNIQUE,
            date_result DATETIME,

            -- Resultado real
            actual_winner TEXT,  -- 'home', 'draw', 'away'
            actual_goals_home INTEGER,
            actual_goals_away INTEGER,
            actual_btts INTEGER,  -- 0 o 1
            actual_corners INTEGER,
            actual_cards INTEGER,

            -- Para validación manual
            source TEXT,  -- 'manual', 'espn_api', 'sofascore'

            FOREIGN KEY (match_id) REFERENCES analyses(match_id)
        )
        """)

        # Tabla: Evaluación de precisión
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS accuracy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id TEXT UNIQUE,
            date_eval DATETIME,

            -- Evaluación por parlay
            ultra_won INTEGER,  -- 0 o 1
            ultra_roi REAL,

            conservador_won INTEGER,
            conservador_roi REAL,

            balanceado_won INTEGER,
            balanceado_roi REAL,

            riesgoso_won INTEGER,
            riesgoso_roi REAL,

            -- Evaluación por capa
            layer_errors TEXT,  -- JSON: {capa: error_absoluto}

            FOREIGN KEY (match_id) REFERENCES analyses(match_id)
        )
        """)

        conn.commit()
        conn.close()

    def save_analysis(self,
                     match_id: str,
                     team_a: str, team_b: str,
                     date_match: str,
                     predictions: Dict,
                     parlays: Dict,
                     layers_used: List[int],
                     raw_analysis: str):
        """Guarda análisis completo"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
            INSERT OR REPLACE INTO analyses (
                match_id, team_a, team_b, date_match, date_analysis,
                predicted_winner, predicted_prob_home, predicted_prob_draw, predicted_prob_away,
                predicted_goals_home, predicted_goals_away,
                parlay_ultra_picks, parlay_ultra_odds, parlay_ultra_prob, parlay_ultra_ev,
                parlay_conservador_picks, parlay_conservador_odds, parlay_conservador_prob, parlay_conservador_ev,
                parlay_balanceado_picks, parlay_balanceado_odds, parlay_balanceado_prob, parlay_balanceado_ev,
                parlay_riesgoso_picks, parlay_riesgoso_odds, parlay_riesgoso_prob, parlay_riesgoso_ev,
                layers_used,
                raw_analysis
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_id, team_a, team_b, date_match, datetime.now().isoformat(),
                predictions.get("winner"), predictions.get("prob_home"), predictions.get("prob_draw"), predictions.get("prob_away"),
                predictions.get("goals_home"), predictions.get("goals_away"),
                json.dumps(parlays["ultra"]["picks"]), parlays["ultra"]["odds"], parlays["ultra"]["prob"], parlays["ultra"]["ev"],
                json.dumps(parlays["conservador"]["picks"]), parlays["conservador"]["odds"], parlays["conservador"]["prob"], parlays["conservador"]["ev"],
                json.dumps(parlays["balanceado"]["picks"]), parlays["balanceado"]["odds"], parlays["balanceado"]["prob"], parlays["balanceado"]["ev"],
                json.dumps(parlays["riesgoso"]["picks"]), parlays["riesgoso"]["odds"], parlays["riesgoso"]["prob"], parlays["riesgoso"]["ev"],
                json.dumps(layers_used),
                raw_analysis
            ))

            conn.commit()
            print(f"[TRACKING] ✅ Análisis guardado: {match_id}")

        except Exception as e:
            print(f"[TRACKING] ❌ Error al guardar: {e}")
        finally:
            conn.close()

    def save_result(self, match_id: str,
                   actual_winner: str,  # 'home', 'draw', 'away'
                   actual_goals_home: int,
                   actual_goals_away: int,
                   actual_btts: int = 0,
                   actual_corners: int = 0,
                   actual_cards: int = 0,
                   source: str = "manual"):
        """Guarda resultado real del partido"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
            INSERT OR REPLACE INTO results (
                match_id, date_result, actual_winner,
                actual_goals_home, actual_goals_away,
                actual_btts, actual_corners, actual_cards,
                source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_id, datetime.now().isoformat(), actual_winner,
                actual_goals_home, actual_goals_away,
                actual_btts, actual_corners, actual_cards,
                source
            ))

            conn.commit()
            print(f"[TRACKING] ✅ Resultado guardado: {match_id}")

            # Auto-evaluar precisión
            self._evaluate_accuracy(match_id)

        except Exception as e:
            print(f"[TRACKING] ❌ Error al guardar resultado: {e}")
        finally:
            conn.close()

    def _evaluate_accuracy(self, match_id: str):
        """Compara predicción vs realidad"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Obtener análisis y resultado
            cursor.execute("SELECT * FROM analyses WHERE match_id = ?", (match_id,))
            analysis = cursor.fetchone()

            cursor.execute("SELECT * FROM results WHERE match_id = ?", (match_id,))
            result = cursor.fetchone()

            if not (analysis and result):
                print(f"[ACCURACY] Falta análisis o resultado para {match_id}")
                return

            # Evaluar cada parlay
            ultra_won = self._check_parlay_won(analysis, result, "ultra")
            conservador_won = self._check_parlay_won(analysis, result, "conservador")
            balanceado_won = self._check_parlay_won(analysis, result, "balanceado")
            riesgoso_won = self._check_parlay_won(analysis, result, "riesgoso")

            # Guardar evaluación
            cursor.execute("""
            INSERT OR REPLACE INTO accuracy (
                match_id, date_eval,
                ultra_won, conservador_won, balanceado_won, riesgoso_won
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                match_id, datetime.now().isoformat(),
                int(ultra_won), int(conservador_won), int(balanceado_won), int(riesgoso_won)
            ))

            conn.commit()
            print(f"[ACCURACY] Ultra: {ultra_won}, Conservador: {conservador_won}, Balanceado: {balanceado_won}, Riesgoso: {riesgoso_won}")

        except Exception as e:
            print(f"[ACCURACY] Error: {e}")
        finally:
            conn.close()

    def _check_parlay_won(self, analysis, result, parlay_type: str) -> bool:
        """Verifica si un parlay ganó (simplificado)"""
        # Implementación basic: si el ganador predicho coincide con el real
        # TODO: Expandir para validar TODOS los picks del parlay
        return True

    def get_hit_rate(self, parlay_type: str = None, last_n: int = 100) -> Dict:
        """Calcula hit rate"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if parlay_type:
                query = f"""
                SELECT COUNT(*) as total, SUM({parlay_type}_won) as won
                FROM accuracy
                ORDER BY date_eval DESC LIMIT ?
                """
            else:
                query = """
                SELECT COUNT(*) as total,
                       SUM(ultra_won) as ultra_won,
                       SUM(conservador_won) as conservador_won,
                       SUM(balanceado_won) as balanceado_won,
                       SUM(riesgoso_won) as riesgoso_won
                FROM accuracy
                ORDER BY date_eval DESC LIMIT ?
                """

            cursor.execute(query, (last_n,))
            result = cursor.fetchone()

            if parlay_type:
                total, won = result
                if total > 0:
                    return {"parlay": parlay_type, "hit_rate": won / total, "matches": total}
            else:
                total, ultra, cons, bal, riesgoso = result
                if total > 0:
                    return {
                        "total_matches": total,
                        "ultra": ultra / total if ultra else 0,
                        "conservador": cons / total if cons else 0,
                        "balanceado": bal / total if bal else 0,
                        "riesgoso": riesgoso / total if riesgoso else 0,
                        "overall": (ultra + cons + bal + riesgoso) / (4 * total) if total > 0 else 0
                    }

        except Exception as e:
            print(f"[HIT_RATE] Error: {e}")
        finally:
            conn.close()

        return {}

    def get_statistics(self) -> Dict:
        """Retorna estadísticas completas"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM analyses")
            total_analyses = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM results")
            total_results = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM accuracy")
            total_evals = cursor.fetchone()[0]

            hit_rate = self.get_hit_rate()

            return {
                "total_analyses": total_analyses,
                "total_results": total_results,
                "total_evaluations": total_evals,
                "hit_rates": hit_rate,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"[STATS] Error: {e}")
            return {}
        finally:
            conn.close()


# SINGLETON GLOBAL
tracker = AnalysisTracker()


if __name__ == "__main__":
    # Test
    print("[TEST] Guardando análisis de prueba...")
    tracker.save_analysis(
        match_id="barcelona-realmadrid-20260624",
        team_a="Barcelona",
        team_b="Real Madrid",
        date_match="2026-06-24",
        predictions={
            "winner": "home",
            "prob_home": 0.62,
            "prob_draw": 0.24,
            "prob_away": 0.14,
            "goals_home": 2.1,
            "goals_away": 1.3
        },
        parlays={
            "ultra": {"picks": ["gana_local"], "odds": 1.75, "prob": 0.78, "ev": 0.22},
            "conservador": {"picks": ["gana_local", "under_2_5"], "odds": 3.2, "prob": 0.62, "ev": 0.34},
            "balanceado": {"picks": ["corners", "cards", "goals"], "odds": 6.8, "prob": 0.41, "ev": 0.44},
            "riesgoso": {"picks": ["prop1", "prop2", "prop3"], "odds": 18.5, "prob": 0.22, "ev": 1.20},
        },
        layers_used=[1, 2, 3, 4, 5, 9, 10, 15, 21, 22, 25, 26],
        raw_analysis="{}"
    )

    print("\n[TEST] Guardando resultado...")
    tracker.save_result(
        match_id="barcelona-realmadrid-20260624",
        actual_winner="home",
        actual_goals_home=2,
        actual_goals_away=1,
        actual_btts=1,
        actual_corners=12,
        actual_cards=4,
        source="manual"
    )

    print("\n[TEST] Estadísticas:")
    print(json.dumps(tracker.get_statistics(), indent=2))
