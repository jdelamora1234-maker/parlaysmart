"""
ADVANCED RISK MANAGEMENT - Gestión inteligente de bankroll y riesgo
Features:
  - Dynamic stake sizing basado en confianza
  - Exposure limits por mercado
  - Drawdown protection
  - Win-rate tracking
  - Kelly Criterion adaptativo
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class AdvancedRiskManager:
    """Gestión avanzada de riesgo y bankroll"""

    def __init__(self, starting_bankroll: float = 1000.0):
        self.starting_bankroll = starting_bankroll
        self.current_bankroll = starting_bankroll
        self.bets_history = []
        self.exposure = defaultdict(float)  # market -> exposure
        self.daily_limits = {"loss": 50, "win": 500}  # Daily P&L limits

    def calculate_dynamic_stake(self,
                               confidence: float,
                               odds: float,
                               kelly_fraction: float = 0.5) -> float:
        """
        Calcula stake dinámico basado en confianza

        Confianza baja (0.5): conservative sizing
        Confianza alta (0.9): aggressive sizing
        """

        # Base Kelly
        kelly_pct = kelly_fraction * min(0.25, 0.1 + (confidence - 0.5) * 0.3)

        # Ajustar por bankroll
        max_stake = self.current_bankroll * kelly_pct

        # Ajustar por drawdown
        max_drawdown_pct = self._estimate_drawdown_risk()
        if max_drawdown_pct > 0.20:  # Si perdimos > 20%
            max_stake *= 0.5  # Reducir apuestas a mitad

        # Mínimo y máximo
        min_stake = max(10, self.current_bankroll * 0.01)
        max_stake = min(max_stake, self.current_bankroll * 0.10)

        return round(max_stake, 2)

    def check_exposure_limit(self, market: str, stake: float,
                            max_exposure_pct: float = 0.30) -> bool:
        """
        Verifica si el stake respeta límites de exposición

        No más del 30% del bankroll expuesto en un mercado
        """

        new_exposure = self.exposure[market] + stake
        max_allowed = self.current_bankroll * max_exposure_pct

        return new_exposure <= max_allowed

    def validate_bet(self, bet: Dict) -> Tuple[bool, str]:
        """
        Valida una apuesta contra todas las reglas

        Retorna: (valid, reason)
        """

        # 1. Stake size check
        if bet.get("stake", 0) > self.current_bankroll * 0.10:
            return False, "Stake exceeds 10% bankroll limit"

        # 2. Exposure check
        market = bet.get("market", "general")
        if not self.check_exposure_limit(market, bet.get("stake", 0)):
            return False, f"Exposure limit exceeded for {market}"

        # 3. Daily loss limit
        daily_loss = self._calculate_daily_loss()
        if daily_loss + bet.get("stake", 0) > self.daily_limits["loss"]:
            return False, "Daily loss limit would be exceeded"

        # 4. Confidence check
        if bet.get("confidence", 0) < 0.50:
            return False, "Confidence too low (< 50%)"

        # 5. Odds check
        if bet.get("odds", 1.0) < 1.01:
            return False, "Odds too low (< 1.01)"

        return True, "Valid bet"

    def record_result(self, match_id: str, bet_data: Dict, result: str):
        """
        Registra el resultado de una apuesta

        result: "win", "loss", "void"
        """

        timestamp = datetime.now()
        stake = bet_data.get("stake", 0)
        odds = bet_data.get("odds", 1.0)

        pnl = 0
        if result == "win":
            pnl = stake * (odds - 1)
        elif result == "loss":
            pnl = -stake

        self.bets_history.append({
            "match_id": match_id,
            "timestamp": timestamp.isoformat(),
            "stake": stake,
            "odds": odds,
            "result": result,
            "pnl": pnl,
            "confidence": bet_data.get("confidence", 0.5),
            "market": bet_data.get("market", "general"),
        })

        # Actualizar bankroll
        self.current_bankroll += pnl

        # Actualizar exposición
        market = bet_data.get("market", "general")
        self.exposure[market] -= stake

    def get_winrate_by_confidence(self) -> Dict[str, Dict]:
        """
        Calcula win rate por nivel de confianza

        Ayuda a entender qué niveles de confianza funcionan
        """

        confidence_buckets = {
            "low": (0.50, 0.60),
            "medium": (0.60, 0.75),
            "high": (0.75, 0.90),
            "very_high": (0.90, 1.00),
        }

        results = {}

        for bucket_name, (min_conf, max_conf) in confidence_buckets.items():
            bets = [b for b in self.bets_history
                   if min_conf <= b["confidence"] < max_conf]

            if not bets:
                continue

            wins = sum(1 for b in bets if b["result"] == "win")
            total_pnl = sum(b["pnl"] for b in bets)

            results[bucket_name] = {
                "count": len(bets),
                "wins": wins,
                "winrate": round(wins / len(bets), 3) if bets else 0,
                "total_pnl": round(total_pnl, 2),
                "avg_pnl": round(total_pnl / len(bets), 2) if bets else 0,
            }

        return results

    def calculate_kelly_adaptive(self) -> float:
        """
        Calcula Kelly adaptativo basado en winrate real

        Si winrate real < expected: reducir Kelly
        Si winrate real > expected: aumentar Kelly (levemente)
        """

        if len(self.bets_history) < 20:
            return 0.50  # Conservador hasta tener data

        recent = self.bets_history[-50:]  # Últimas 50 apuestas

        wins = sum(1 for b in recent if b["result"] == "win")
        winrate = wins / len(recent)

        # Expected basado en confianza promedio
        avg_confidence = sum(b["confidence"] for b in recent) / len(recent)
        expected_winrate = avg_confidence

        # Adaptar
        if winrate < expected_winrate - 0.05:  # Más de 5pp por debajo
            return 0.25  # Muy conservador
        elif winrate < expected_winrate:
            return 0.35  # Conservador
        elif winrate > expected_winrate + 0.05:
            return 0.75  # Agresivo
        else:
            return 0.50  # Neutral

    def get_portfolio_summary(self) -> Dict:
        """Resumen completo del portafolio"""

        if not self.bets_history:
            return {
                "total_bets": 0,
                "winrate": 0,
                "current_bankroll": self.current_bankroll,
                "roi": 0,
            }

        wins = sum(1 for b in self.bets_history if b["result"] == "win")
        total_pnl = sum(b["pnl"] for b in self.bets_history)
        roi = (total_pnl / self.starting_bankroll) * 100

        # Drawdown
        max_bankroll = self.starting_bankroll
        max_drawdown = 0
        for b in self.bets_history:
            max_bankroll = max(max_bankroll, self.current_bankroll)
            drawdown = (max_bankroll - self.current_bankroll) / max_bankroll
            max_drawdown = max(max_drawdown, drawdown)

        return {
            "total_bets": len(self.bets_history),
            "wins": wins,
            "losses": len(self.bets_history) - wins,
            "winrate": round(wins / len(self.bets_history), 3) if self.bets_history else 0,
            "current_bankroll": round(self.current_bankroll, 2),
            "starting_bankroll": self.starting_bankroll,
            "total_pnl": round(total_pnl, 2),
            "roi_pct": round(roi, 2),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "kelly_adaptive": round(self.calculate_kelly_adaptive(), 2),
        }

    def _estimate_drawdown_risk(self) -> float:
        """Estima riesgo de drawdown basado en últimas apuestas"""

        if not self.bets_history:
            return 0

        recent = self.bets_history[-20:]
        losses = sum(1 for b in recent if b["result"] == "loss")

        loss_streak = 0
        for b in reversed(self.bets_history[-10:]):
            if b["result"] == "loss":
                loss_streak += 1
            else:
                break

        if loss_streak >= 5:
            return 0.30  # Racha perdedora
        elif losses / len(recent) > 0.50:
            return 0.20  # Más pérdidas que ganancias

        return 0.05  # Bajo riesgo

    def _calculate_daily_loss(self) -> float:
        """Calcula pérdida acumulada hoy"""

        today = datetime.now().date()
        today_bets = [b for b in self.bets_history
                     if datetime.fromisoformat(b["timestamp"]).date() == today
                     and b["result"] == "loss"]

        return sum(b["pnl"] for b in today_bets)


# Singleton
from collections import defaultdict
risk_manager = AdvancedRiskManager()


if __name__ == "__main__":
    print("[TEST] Advanced Risk Manager\n")

    # Test dynamic stake
    stake = risk_manager.calculate_dynamic_stake(confidence=0.80, odds=3.2)
    print(f"Dynamic stake (80% confidence): ${stake}\n")

    # Test bet validation
    bet = {
        "stake": 50,
        "odds": 2.5,
        "confidence": 0.75,
        "market": "football"
    }

    valid, reason = risk_manager.validate_bet(bet)
    print(f"Bet validation: {valid} - {reason}\n")

    # Simular resultados
    print("Simulating 10 bets...")
    import random
    for i in range(10):
        result = "win" if random.random() < 0.65 else "loss"
        risk_manager.record_result(
            f"match_{i}",
            bet,
            result
        )

    # Resumen
    summary = risk_manager.get_portfolio_summary()
    print(f"\nPortfolio Summary:")
    print(json.dumps(summary, indent=2))
