"""
REALTIME ALERTS SYSTEM - Notificaciones automáticas de oportunidades
Detecta y alerta: Value bets, Sharp moves, Line changes, Arbitrage
"""

from datetime import datetime
from typing import Dict, List, Callable
import json

class RealtimeAlertsSystem:
    """Sistema de alertas en tiempo real"""

    def __init__(self):
        self.alerts = []
        self.subscribers = []  # Callbacks para notificaciones
        self.alert_queue = []
        self.alert_levels = {
            "critical": 1,  # Arbitrage, major sharp move
            "high": 2,      # Strong value bet
            "medium": 3,    # Decent opportunity
            "low": 4,       # Marginal value
        }

    def subscribe(self, callback: Callable):
        """Suscribir a notificaciones"""
        self.subscribers.append(callback)

    def _notify_subscribers(self, alert: Dict):
        """Notifica a todos los suscriptores"""
        for callback in self.subscribers:
            try:
                callback(alert)
            except Exception as e:
                print(f"Error notifying subscriber: {e}")

    def alert_value_bet(self, match_id: str, parlay_type: str,
                        confidence: float, edge_pct: float, odds: float):
        """Alerta: Value bet detectado"""

        # Determinar level
        if edge_pct > 15 and confidence > 0.85:
            level = "critical"
        elif edge_pct > 10 and confidence > 0.75:
            level = "high"
        elif edge_pct > 5 and confidence > 0.65:
            level = "medium"
        else:
            level = "low"

        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": "VALUE_BET",
            "level": level,
            "match_id": match_id,
            "parlay_type": parlay_type,
            "edge_pct": round(edge_pct, 2),
            "confidence": round(confidence, 2),
            "odds": round(odds, 2),
            "action": f"BET {parlay_type} at {odds}",
        }

        self.alerts.append(alert)
        self._notify_subscribers(alert)

        return alert

    def alert_sharp_move(self, match_id: str, outcome: str,
                        direction: str, change_pct: float, urgency: str = "medium"):
        """Alerta: Sharp money detectado"""

        if urgency == "high" or abs(change_pct) > 10:
            level = "critical"
        elif abs(change_pct) > 5:
            level = "high"
        else:
            level = "medium"

        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": "SHARP_MOVE",
            "level": level,
            "match_id": match_id,
            "outcome": outcome,
            "direction": direction,
            "change_pct": round(change_pct, 2),
            "message": f"SHARP {direction.upper()}: {outcome} moved {abs(change_pct):.1f}%",
        }

        self.alerts.append(alert)
        self._notify_subscribers(alert)

        return alert

    def alert_line_change(self, match_id: str, outcome: str,
                         old_odds: float, new_odds: float):
        """Alerta: Cambio significativo de línea"""

        change_pct = ((new_odds - old_odds) / old_odds) * 100

        if abs(change_pct) > 3:
            level = "high"
        elif abs(change_pct) > 1:
            level = "medium"
        else:
            return None  # No alert for small changes

        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": "LINE_CHANGE",
            "level": level,
            "match_id": match_id,
            "outcome": outcome,
            "old_odds": round(old_odds, 2),
            "new_odds": round(new_odds, 2),
            "change_pct": round(change_pct, 2),
            "direction": "UP" if change_pct > 0 else "DOWN",
        }

        self.alerts.append(alert)
        self._notify_subscribers(alert)

        return alert

    def alert_arbitrage(self, match_id: str, arbitrage_margin: float,
                       odds_dict: Dict[str, float]):
        """Alerta: Oportunidad de arbitrage"""

        level = "critical" if arbitrage_margin > 0.05 else "high"

        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": "ARBITRAGE",
            "level": level,
            "match_id": match_id,
            "arbitrage_margin_pct": round(arbitrage_margin * 100, 2),
            "odds": odds_dict,
            "action": f"GUARANTEED PROFIT: {arbitrage_margin*100:.2f}%",
        }

        self.alerts.append(alert)
        self._notify_subscribers(alert)

        return alert

    def alert_correlation_warning(self, match_id: str, correlation: float,
                                 picks: List[str]):
        """Alerta: Selecciones altamente correlacionadas"""

        if abs(correlation) > 0.8:
            level = "high"
        elif abs(correlation) > 0.6:
            level = "medium"
        else:
            return None

        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": "CORRELATION_WARNING",
            "level": level,
            "match_id": match_id,
            "correlation": round(correlation, 3),
            "picks": picks,
            "warning": f"Picks are {abs(correlation)*100:.0f}% correlated - parlay risk",
        }

        self.alerts.append(alert)
        self._notify_subscribers(alert)

        return alert

    def get_alerts_by_level(self, level: str, match_id: str = None) -> List[Dict]:
        """Obtiene alertas por nivel de severidad"""

        filtered = [a for a in self.alerts if a["level"] == level]

        if match_id:
            filtered = [a for a in filtered if a.get("match_id") == match_id]

        return filtered

    def get_critical_alerts(self) -> List[Dict]:
        """Obtiene solo alertas críticas"""
        return self.get_alerts_by_level("critical")

    def clear_old_alerts(self, hours: int = 24):
        """Limpia alertas más viejas que N horas"""

        cutoff = datetime.now().timestamp() - (hours * 3600)

        self.alerts = [
            a for a in self.alerts
            if datetime.fromisoformat(a["timestamp"]).timestamp() > cutoff
        ]

    def get_summary(self) -> Dict:
        """Resumen de alertas recientes"""

        by_level = {}
        by_type = {}

        for alert in self.alerts[-100:]:  # Últimas 100
            level = alert.get("level")
            alert_type = alert.get("type")

            by_level[level] = by_level.get(level, 0) + 1
            by_type[alert_type] = by_type.get(alert_type, 0) + 1

        return {
            "total_alerts": len(self.alerts),
            "by_level": by_level,
            "by_type": by_type,
            "critical_alerts": len(self.get_critical_alerts()),
        }


# Singleton
alerts_system = RealtimeAlertsSystem()


# Example callback para console logging
def console_logger(alert: Dict):
    """Callback que imprime alertas en consola"""
    level_emoji = {
        "critical": "🚨",
        "high": "⚠️",
        "medium": "ℹ️",
        "low": "💡",
    }

    emoji = level_emoji.get(alert.get("level"), "📢")

    print(f"\n{emoji} [{alert.get('type')}] {alert.get('timestamp', '')}")
    print(f"   Match: {alert.get('match_id')}")
    print(f"   Action: {alert.get('action') or alert.get('warning') or alert.get('message')}")


if __name__ == "__main__":
    print("[TEST] Realtime Alerts System\n")

    # Suscribir logger
    alerts_system.subscribe(console_logger)

    # Test alerts
    print("Triggering test alerts...\n")

    alerts_system.alert_value_bet(
        "barcelona-realmadrid",
        "ultra",
        confidence=0.85,
        edge_pct=12.5,
        odds=2.0
    )

    alerts_system.alert_sharp_move(
        "barcelona-realmadrid",
        "home",
        direction="down",
        change_pct=7.5,
        urgency="high"
    )

    alerts_system.alert_arbitrage(
        "barcelona-realmadrid",
        arbitrage_margin=0.06,
        odds_dict={"home": 1.95, "draw": 3.20, "away": 3.50}
    )

    # Summary
    print("\n" + "="*50)
    summary = alerts_system.get_summary()
    print(f"Alerts Summary: {json.dumps(summary, indent=2)}")
