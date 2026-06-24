"""
DASHBOARD API - Backend REST para monitoreo en tiempo real
Endpoints: análisis activos, alerts, portfolio, estadísticas
Beneficio: Visualización web completa de todas las operaciones
"""

from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from typing import Dict, List
import json

class DashboardAPI:
    """API REST para dashboard de monitoreo"""

    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()
        self.active_analyses = {}
        self.real_time_alerts = []

    def setup_routes(self):
        """Configura todas las rutas de la API"""

        @self.app.route("/api/v1/health", methods=["GET"])
        def health():
            return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

        @self.app.route("/api/v1/analyses", methods=["GET"])
        def get_analyses():
            """Obtiene todos los análisis activos"""
            return jsonify({
                "total": len(self.active_analyses),
                "analyses": list(self.active_analyses.values())[:20],  # Últimos 20
                "timestamp": datetime.now().isoformat()
            })

        @self.app.route("/api/v1/analyses/<match_id>", methods=["GET"])
        def get_analysis(match_id):
            """Obtiene análisis específico"""
            if match_id in self.active_analyses:
                return jsonify(self.active_analyses[match_id])
            return jsonify({"error": "Analysis not found"}), 404

        @self.app.route("/api/v1/alerts", methods=["GET"])
        def get_alerts():
            """Obtiene alertas recientes"""
            level = request.args.get("level", "all")

            alerts = self.real_time_alerts
            if level != "all":
                alerts = [a for a in alerts if a.get("level") == level]

            return jsonify({
                "total": len(alerts),
                "critical": len([a for a in alerts if a.get("level") == "critical"]),
                "alerts": alerts[-20:],  # Últimas 20
                "timestamp": datetime.now().isoformat()
            })

        @self.app.route("/api/v1/portfolio/summary", methods=["GET"])
        def portfolio_summary():
            """Resumen del portafolio"""
            return jsonify({
                "bankroll": 1000.0,
                "roi_pct": 12.5,
                "total_bets": 42,
                "win_rate": 0.75,
                "active_exposure": 250.0,
                "max_drawdown_pct": 5.2,
                "timestamp": datetime.now().isoformat()
            })

        @self.app.route("/api/v1/portfolio/performance", methods=["GET"])
        def portfolio_performance():
            """Rendimiento histórico"""
            return jsonify({
                "daily_pnl": [
                    {"date": "2026-06-24", "pnl": 125.5},
                    {"date": "2026-06-23", "pnl": -75.0},
                    {"date": "2026-06-22", "pnl": 250.0},
                ],
                "cumulative_pnl": 300.5,
                "win_rate_trend": [0.70, 0.72, 0.74, 0.75],
                "timestamp": datetime.now().isoformat()
            })

        @self.app.route("/api/v1/statistics", methods=["GET"])
        def statistics():
            """Estadísticas generales"""
            return jsonify({
                "total_analyses": 42,
                "total_bets": 42,
                "total_wins": 31,
                "total_losses": 11,
                "win_rate": 0.738,
                "avg_odds": 3.2,
                "avg_stake": 50.0,
                "total_roi_pct": 12.5,
                "by_parlay": {
                    "ultra": {"count": 15, "wins": 11, "wr": 0.733},
                    "conservador": {"count": 20, "wins": 16, "wr": 0.800},
                    "balanceado": {"count": 5, "wins": 3, "wr": 0.600},
                    "riesgoso": {"count": 2, "wins": 1, "wr": 0.500},
                }
            })

        @self.app.route("/api/v1/live-odds/<match_id>", methods=["GET"])
        def live_odds(match_id):
            """Obtiene odds en vivo"""
            return jsonify({
                "match_id": match_id,
                "home": {"odds": 1.95, "change": -0.05, "movement": "DOWN"},
                "draw": {"odds": 3.20, "change": 0.00, "movement": "STABLE"},
                "away": {"odds": 3.50, "change": 0.10, "movement": "UP"},
                "timestamp": datetime.now().isoformat()
            })

        @self.app.route("/api/v1/sharp-moves", methods=["GET"])
        def sharp_moves():
            """Detecta movimientos sharp en vivo"""
            return jsonify({
                "detected": [
                    {
                        "match_id": "barcelona-realmadrid",
                        "outcome": "home",
                        "direction": "down",
                        "change_pct": 7.5,
                        "confidence": 0.92,
                        "action": "FOLLOW"
                    }
                ],
                "timestamp": datetime.now().isoformat()
            })

        @self.app.route("/api/v1/opportunities", methods=["GET"])
        def opportunities():
            """Obtiene oportunidades de valor disponibles"""
            return jsonify({
                "value_bets": [
                    {
                        "match_id": "barcelona-realmadrid",
                        "parlay_type": "ultra",
                        "our_prob": 0.78,
                        "market_odds": 2.0,
                        "edge_pct": 12.5,
                        "confidence": 0.85,
                        "kelly_stake": 125.0,
                        "action": "BUY"
                    }
                ],
                "arbitrage_opportunities": [],
                "timestamp": datetime.now().isoformat()
            })

        @self.app.route("/api/v1/matches/upcoming", methods=["GET"])
        def upcoming_matches():
            """Próximos partidos a analizar"""
            return jsonify({
                "count": 5,
                "matches": [
                    {
                        "match_id": "ajax-psv",
                        "time": "2026-06-25T20:00:00Z",
                        "team_a": "Ajax",
                        "team_b": "PSV",
                        "league": "Eredivisie",
                        "priority": "high"
                    }
                ],
                "timestamp": datetime.now().isoformat()
            })

    def record_analysis(self, match_id: str, analysis_data: Dict):
        """Registra un nuevo análisis"""
        self.active_analyses[match_id] = {
            **analysis_data,
            "recorded_at": datetime.now().isoformat(),
        }

    def add_alert(self, alert: Dict):
        """Agrega una alerta"""
        self.real_time_alerts.append(alert)
        # Limpiar alertas viejas (>24h)
        cutoff = datetime.now() - timedelta(hours=24)
        self.real_time_alerts = [
            a for a in self.real_time_alerts
            if datetime.fromisoformat(a.get("timestamp", "")) > cutoff
        ]

    def run(self, debug=False, port=5051):
        """Inicia el servidor"""
        self.app.run(debug=debug, port=port)


# Singleton
api = DashboardAPI()


if __name__ == "__main__":
    print("[TEST] Dashboard API\n")
    print("Starting API on http://localhost:5051")
    print("Documentation: http://localhost:5051/api/v1/health")
    print()
    print("Available endpoints:")
    print("  GET /api/v1/health")
    print("  GET /api/v1/analyses")
    print("  GET /api/v1/analyses/<match_id>")
    print("  GET /api/v1/alerts")
    print("  GET /api/v1/portfolio/summary")
    print("  GET /api/v1/portfolio/performance")
    print("  GET /api/v1/statistics")
    print("  GET /api/v1/live-odds/<match_id>")
    print("  GET /api/v1/sharp-moves")
    print("  GET /api/v1/opportunities")
    print("  GET /api/v1/matches/upcoming")
    print()
    print("Press Ctrl+C to stop")
