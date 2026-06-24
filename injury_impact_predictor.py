"""
INJURY IMPACT PREDICTOR - Impacto de lesiones en tiempo real
Beneficio: Detectar cambios de línea por lesiones ANTES que mercado
Estrategia: Monitorear noticias, calcular impacto
"""

from typing import Dict, List, Tuple
from datetime import datetime

class InjuryImpactPredictor:
    """Predice impacto de lesiones en partidos"""

    def __init__(self):
        self.injury_database = {}
        self.player_impact_ratings = {}
        self.historical_impacts = []

    def estimate_player_importance(self,
                                  team: str,
                                  player_name: str,
                                  position: str,
                                  stats: Dict) -> float:
        """
        Estima la importancia de un jugador al equipo

        Basado en: goles, asistencias, time played, marketvalue
        """

        importance_score = 0.0

        # Posición base
        position_weights = {
            "GK": 0.8,
            "DEF": 0.5,
            "MID": 0.7,
            "FWD": 0.9,
        }

        importance_score += position_weights.get(position, 0.5)

        # Contribución de goles
        goals = stats.get("goals", 0)
        importance_score += min(goals / 20, 0.3)  # Cap at 0.3

        # Contribución de asistencias
        assists = stats.get("assists", 0)
        importance_score += min(assists / 10, 0.2)  # Cap at 0.2

        # Minutos jugados (regularidad)
        minutes_pct = stats.get("minutes_pct", 0.5)
        importance_score += minutes_pct * 0.2

        # Capped at 1.0
        return min(importance_score, 1.0)

    def calculate_injury_impact_on_odds(self,
                                       player_importance: float,
                                       injury_type: str,
                                       team_home: bool = True) -> Dict[str, float]:
        """
        Calcula impacto de una lesión en las odds

        injury_type: "out_for_season", "2_weeks", "doubtful", "questionable"
        """

        # Base impact por tipo de lesión
        injury_impacts = {
            "out_for_season": 0.15,      # -15% odds para ese equipo
            "out_6_weeks": 0.10,
            "out_2_weeks": 0.05,
            "doubtful": 0.03,
            "questionable": 0.01,
        }

        base_impact = injury_impacts.get(injury_type, 0.05)

        # Total impact = base × importance
        total_impact = base_impact * player_importance

        # Si es en casa, impact es 20% mayor
        if team_home:
            total_impact *= 1.2

        # Distribución de impacto entre outcomes
        return {
            "home_win_impact": round(-total_impact if team_home else total_impact * 0.6, 3),
            "draw_impact": round(-total_impact * 0.3, 3),
            "away_win_impact": round(total_impact if team_home else -total_impact, 3),
            "total_impact_pct": round(total_impact * 100, 2),
            "injury_severity": injury_type,
            "player_importance": round(player_importance, 2),
        }

    def injury_cascade_detector(self,
                               injuries: List[Dict],
                               team: str) -> Dict:
        """
        Detecta múltiples lesiones en el mismo equipo

        Varias lesiones = impacto multiplicativo
        """

        if not injuries:
            return {"cascade_detected": False}

        total_impact = 0
        injured_positions = {}

        for injury in injuries:
            position = injury.get("position", "UNK")
            importance = injury.get("importance", 0.5)

            total_impact += importance

            injured_positions[position] = injured_positions.get(position, 0) + 1

        # Detectar cascada: múltiples en la misma posición
        cascade_detected = any(count > 1 for count in injured_positions.values())

        if cascade_detected:
            # Si dos defensas lesionados = problema crítico
            severity = "CRITICAL" if total_impact > 1.5 else "HIGH"
        else:
            severity = "MEDIUM" if total_impact > 1.0 else "LOW"

        return {
            "cascade_detected": cascade_detected,
            "injured_positions": injured_positions,
            "total_impact": round(total_impact, 2),
            "severity": severity,
            "recommendation": "AVOID_BETTING" if severity == "CRITICAL" else "MONITOR"
        }

    def predict_line_movement_from_injury(self,
                                         current_odds: Dict[str, float],
                                         injury_impact: Dict[str, float]) -> Dict[str, float]:
        """
        Predice movimiento de línea dada una lesión

        Si impact = -10%, odds deberían bajar ~10%
        """

        predicted_odds = {}

        for outcome, odds in current_odds.items():
            impact = injury_impact.get(f"{outcome}_impact", 0)

            # Nuevas odds después de lesión
            new_odds = odds * (1 + impact)

            predicted_odds[outcome] = round(new_odds, 2)

        return predicted_odds

    def detect_line_lag(self,
                       current_odds: Dict[str, float],
                       predicted_odds: Dict[str, float],
                       lag_threshold: float = 0.05) -> Dict[str, bool]:
        """
        Detecta si el mercado AÚN NO ajustó a lesión

        Si predicted_odds >> current_odds = oportunidad
        """

        lag_detected = {}

        for outcome in current_odds:
            current = current_odds.get(outcome, 0)
            predicted = predicted_odds.get(outcome, 0)

            if current > 0 and predicted > 0:
                diff_pct = abs((predicted - current) / current)

                # Si difference > threshold = mercado no ajustó
                lag_detected[outcome] = diff_pct > lag_threshold

        return lag_detected

    def monitor_injury_news(self,
                           match_id: str,
                           team: str,
                           latest_news: str) -> Dict:
        """
        Monitorea noticias de lesiones para un partido
        """

        # Palabras clave
        injury_keywords = {
            "out": 0.9,
            "injured": 0.8,
            "ruled out": 0.95,
            "doubtful": 0.3,
            "questionable": 0.1,
            "sidelined": 0.85,
            "unavailable": 0.8,
        }

        injury_detected = False
        severity = 0.0

        news_lower = latest_news.lower()

        for keyword, severity_level in injury_keywords.items():
            if keyword in news_lower:
                injury_detected = True
                severity = max(severity, severity_level)

        return {
            "match_id": match_id,
            "team": team,
            "injury_detected": injury_detected,
            "severity": severity,
            "news": latest_news,
            "action": "ALERT_TRADING_DESK" if injury_detected and severity > 0.5 else "MONITOR"
        }

    def get_injury_report(self, match_id: str) -> Dict:
        """Reporte completo de lesiones para un partido"""

        return {
            "match_id": match_id,
            "timestamp": datetime.now().isoformat(),
            "injury_database": self.injury_database,
            "total_injured_players": len(self.injury_database),
            "affected_positions": self._count_positions(),
            "overall_impact": "NORMAL" if len(self.injury_database) == 0 else "ELEVATED",
        }

    def _count_positions(self) -> Dict[str, int]:
        """Cuenta jugadores lesionados por posición"""
        positions = {}

        for injury_info in self.injury_database.values():
            pos = injury_info.get("position", "UNK")
            positions[pos] = positions.get(pos, 0) + 1

        return positions


# Singleton
injury_predictor = InjuryImpactPredictor()


if __name__ == "__main__":
    print("[TEST] Injury Impact Predictor\n")

    # Test 1: Player importance
    print("Test 1: Player Importance Rating")
    importance = injury_predictor.estimate_player_importance(
        "Barcelona",
        "Lewandowski",
        "FWD",
        {"goals": 18, "assists": 5, "minutes_pct": 0.95}
    )
    print(f"Lewandowski importance: {importance:.2f} (out of 1.0)\n")

    # Test 2: Injury impact
    print("Test 2: Injury Impact on Odds")
    impact = injury_predictor.calculate_injury_impact_on_odds(
        player_importance=importance,
        injury_type="out_for_season",
        team_home=True
    )
    print(f"If Lewandowski out: {impact}\n")

    # Test 3: Line movement
    print("Test 3: Predicted Line Movement")
    current = {"home": 1.95, "draw": 3.20, "away": 3.50}
    predicted = injury_predictor.predict_line_movement_from_injury(current, impact)
    print(f"Current odds: {current}")
    print(f"After injury: {predicted}\n")

    # Test 4: Injury news monitoring
    print("Test 4: Injury News Monitoring")
    news_result = injury_predictor.monitor_injury_news(
        "barcelona-realmadrid",
        "Barcelona",
        "Lewandowski ruled out for rest of season with knee injury"
    )
    print(f"Detection: {news_result['injury_detected']}")
    print(f"Action: {news_result['action']}")
