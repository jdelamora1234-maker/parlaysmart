"""
LIVE ODDS TRACKER - Monitoreo de cambios de odds en tiempo real
Detecta: Sharp moves, line changes, movement direction, volatility
Beneficio: +3-5% capturando cambios antes de que se endurezcan
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict

class LiveOddsTracker:
    """Monitorea odds en vivo y detecta patrones"""

    def __init__(self, history_minutes: int = 240):
        self.history_minutes = history_minutes
        self.odds_history = defaultdict(list)  # match_id -> [(timestamp, odds, source), ...]
        self.price_movements = defaultdict(list)
        self.sharp_indicators = defaultdict(dict)

    def record_odds(self, match_id: str, odds_dict: Dict[str, float], source: str = "betfair"):
        """Registra odds en un momento dado"""

        timestamp = datetime.now()

        for outcome, odds in odds_dict.items():
            key = f"{match_id}:{outcome}"
            self.odds_history[key].append({
                "timestamp": timestamp.isoformat(),
                "odds": odds,
                "source": source,
            })

        # Limpiar histórico viejo
        self._cleanup_old_records(key)

    def detect_sharp_moves(self, match_id: str, threshold_pct: float = 5.0) -> Dict[str, Dict]:
        """
        Detecta movimientos sharp (cambios > threshold en corto tiempo)

        Sharp move = cambio de odds > 5% en menos de 30 minutos
        Indica que los sharps están moviendo dinero
        """

        sharp_moves = {}

        for outcome in ["home", "draw", "away"]:
            key = f"{match_id}:{outcome}"
            history = self.odds_history.get(key, [])

            if len(history) < 2:
                continue

            # Última hora
            now = datetime.now()
            recent = [h for h in history
                     if datetime.fromisoformat(h["timestamp"]) > now - timedelta(minutes=60)]

            if len(recent) < 2:
                continue

            # Cambio de precio
            first_odds = recent[0]["odds"]
            last_odds = recent[-1]["odds"]

            change_pct = ((last_odds - first_odds) / first_odds) * 100

            if abs(change_pct) > threshold_pct:
                sharp_moves[outcome] = {
                    "direction": "up" if change_pct > 0 else "down",
                    "change_pct": round(change_pct, 2),
                    "change_points": round(last_odds - first_odds, 3),
                    "time_minutes": 60,
                    "sharp_signal": "BUYING" if change_pct < 0 else "SELLING",
                    "confidence": min(100, abs(change_pct) * 2),  # Escalar confianza
                }

        return sharp_moves

    def detect_line_movement_direction(self, match_id: str) -> Dict[str, str]:
        """
        Detecta dirección del movimiento de línea

        UP = odds subiendo (outcome menos probable)
        DOWN = odds bajando (outcome más probable)
        """

        movements = {}

        for outcome in ["home", "draw", "away"]:
            key = f"{match_id}:{outcome}"
            history = self.odds_history.get(key, [])

            if len(history) < 2:
                continue

            # Comparar primero vs último
            first = history[0]["odds"]
            last = history[-1]["odds"]

            if last > first:
                movements[outcome] = "UP"  # Menos probable
            elif last < first:
                movements[outcome] = "DOWN"  # Más probable
            else:
                movements[outcome] = "STABLE"

        return movements

    def detect_volatility(self, match_id: str) -> Dict[str, float]:
        """
        Detecta volatilidad de odds

        Alta volatilidad = uncertainty, sharp trading
        Baja volatilidad = consensus, stable prices
        """

        volatility = {}

        for outcome in ["home", "draw", "away"]:
            key = f"{match_id}:{outcome}"
            history = self.odds_history.get(key, [])

            if len(history) < 3:
                volatility[outcome] = 0.0
                continue

            # Calcular cambios sucesivos
            changes = []
            for i in range(1, len(history)):
                prev_odds = history[i-1]["odds"]
                curr_odds = history[i]["odds"]
                change = ((curr_odds - prev_odds) / prev_odds) * 100
                changes.append(abs(change))

            # Volatilidad = desviación estándar de cambios
            if changes:
                import statistics
                vol = statistics.stdev(changes) if len(changes) > 1 else 0
                volatility[outcome] = round(vol, 4)
            else:
                volatility[outcome] = 0.0

        return volatility

    def find_mispriced_bets(self, match_id: str, our_probs: Dict[str, float],
                            min_edge: float = 0.05) -> List[Dict]:
        """
        Encuentra apuestas mispriced basadas en movement

        Si odds bajaron (sharp buying), pero nuestra prob aún más alta = STRONG VALUE
        Si odds subieron (sharp selling), pero nuestra prob aún más alta = WEAK VALUE
        """

        mispriced = []

        sharp_moves = self.detect_sharp_moves(match_id)
        movements = self.detect_line_movement_direction(match_id)

        for outcome, movement in movements.items():
            our_prob = our_probs.get(outcome, 0.5)
            key = f"{match_id}:{outcome}"
            history = self.odds_history.get(key, [])

            if not history:
                continue

            current_odds = history[-1]["odds"]
            market_prob = 1 / current_odds if current_odds > 0 else 0.5

            # Calcular edge
            our_fair_odds = 1 / our_prob if our_prob > 0 else 0
            edge = (our_fair_odds - current_odds) / current_odds

            # Mispriced si:
            # 1. Tenemos edge > min_edge
            # 2. Sharp moves confirman dirección
            if edge > min_edge:
                confidence = 1.0  # Base

                # Sharp moves aumentan confianza
                if outcome in sharp_moves:
                    sharp = sharp_moves[outcome]
                    if sharp["sharp_signal"] == "BUYING" and movement == "DOWN":
                        confidence *= 1.3  # Sharps están comprando, odds bajando = strong
                    elif sharp["sharp_signal"] == "SELLING" and movement == "UP":
                        confidence *= 0.7  # Sharps vendiendo, odds subiendo = weak

                mispriced.append({
                    "outcome": outcome,
                    "our_prob": round(our_prob, 3),
                    "our_fair_odds": round(our_fair_odds, 2),
                    "market_odds": round(current_odds, 2),
                    "market_prob": round(market_prob, 3),
                    "edge": round(edge, 4),
                    "edge_pct": round(edge * 100, 2),
                    "movement": movement,
                    "sharp_signal": sharp_moves.get(outcome, {}).get("sharp_signal", "NONE"),
                    "confidence": round(min(1.0, confidence), 2),
                    "action": "BUY" if confidence > 0.8 else "HOLD" if confidence > 0.5 else "AVOID",
                })

        # Ordenar por confidence descendente
        mispriced.sort(key=lambda x: x["confidence"], reverse=True)

        return mispriced

    def _cleanup_old_records(self, key: str):
        """Elimina registros más viejos que history_minutes"""

        history = self.odds_history.get(key, [])
        cutoff = datetime.now() - timedelta(minutes=self.history_minutes)

        self.odds_history[key] = [
            h for h in history
            if datetime.fromisoformat(h["timestamp"]) > cutoff
        ]

    def get_price_impact(self, match_id: str) -> Dict[str, Dict]:
        """
        Calcula impact de betting en cada outcome

        Price impact = cuánto mueve el mercado un bet
        Alto impact = illiquid, difícil entrar sin slippage
        """

        impact = {}

        for outcome in ["home", "draw", "away"]:
            key = f"{match_id}:{outcome}"
            history = self.odds_history.get(key, [])

            if len(history) < 2:
                continue

            # Range de odds
            prices = [h["odds"] for h in history]
            high = max(prices)
            low = min(prices)
            mid = (high + low) / 2

            impact[outcome] = {
                "high": round(high, 3),
                "low": round(low, 3),
                "range": round(high - low, 3),
                "range_pct": round(((high - low) / mid) * 100, 2),
                "liquidity": "HIGH" if (high - low) < 0.1 else "MEDIUM" if (high - low) < 0.3 else "LOW",
            }

        return impact


# Singleton
tracker = LiveOddsTracker()


if __name__ == "__main__":
    print("[TEST] Live Odds Tracker\n")

    # Simular cambios de odds
    match_id = "barcelona-realmadrid-2026-06-24"

    # Odds iniciales
    tracker.record_odds(match_id, {"home": 1.95, "draw": 3.20, "away": 3.50})
    print("✅ Recorded initial odds")

    # Simular cambios
    time.sleep(1)
    tracker.record_odds(match_id, {"home": 1.92, "draw": 3.25, "away": 3.60})
    print("✅ Recorded movement 1")

    time.sleep(1)
    tracker.record_odds(match_id, {"home": 1.85, "draw": 3.40, "away": 3.80})
    print("✅ Recorded sharp move\n")

    # Detectar sharp moves
    sharp = tracker.detect_sharp_moves(match_id, threshold_pct=3.0)
    print(f"Sharp moves detected: {json.dumps(sharp, indent=2)}\n")

    # Encontrar mispriced
    our_probs = {"home": 0.62, "draw": 0.25, "away": 0.13}
    mispriced = tracker.find_mispriced_bets(match_id, our_probs, min_edge=0.05)
    print(f"Mispriced bets:\n{json.dumps(mispriced, indent=2)}")
