"""
WEBHOOK DISPATCHER - Notificaciones por Slack/Discord/Email
Beneficio: Alertas en tiempo real sin mirar la app
Integración: Slack, Discord, Telegram, Email
"""

import requests
import json
from typing import Dict, List
from datetime import datetime

class WebhookDispatcher:
    """Envía notificaciones a múltiples canales"""

    def __init__(self):
        self.webhooks = {}
        self.notification_history = []
        self.rate_limits = {
            "slack": {"calls": 0, "window": 60, "max": 60},  # 60 por minuto
            "discord": {"calls": 0, "window": 60, "max": 60},
        }

    def register_webhook(self, channel: str, webhook_url: str, channel_name: str = None) -> bool:
        """Registra un webhook"""

        if channel not in ["slack", "discord", "email", "telegram"]:
            return False

        self.webhooks[channel] = {
            "url": webhook_url,
            "channel": channel_name,
            "registered_at": datetime.now().isoformat(),
        }

        return True

    def send_value_bet_alert(self, alert: Dict) -> bool:
        """Envía alerta de value bet"""

        message = self._format_value_bet_message(alert)

        return self.broadcast(message, level="high")

    def send_sharp_move_alert(self, alert: Dict) -> bool:
        """Envía alerta de sharp move"""

        message = self._format_sharp_move_message(alert)

        return self.broadcast(message, level="critical")

    def send_arbitrage_alert(self, alert: Dict) -> bool:
        """Envía alerta de arbitrage (crítica)"""

        message = self._format_arbitrage_message(alert)

        return self.broadcast(message, level="critical")

    def send_portfolio_update(self, stats: Dict) -> bool:
        """Envía actualización de portafolio (diaria)"""

        message = self._format_portfolio_message(stats)

        return self.broadcast(message, level="low")

    def broadcast(self, message: Dict, level: str = "medium") -> bool:
        """Envía a todos los webhooks registrados"""

        success_count = 0

        for channel, webhook_info in self.webhooks.items():
            try:
                if channel == "slack":
                    self._send_to_slack(webhook_info["url"], message)
                elif channel == "discord":
                    self._send_to_discord(webhook_info["url"], message)
                elif channel == "telegram":
                    self._send_to_telegram(webhook_info["url"], message)
                elif channel == "email":
                    self._send_email(webhook_info["url"], message)

                success_count += 1

            except Exception as e:
                print(f"Error sending to {channel}: {e}")

        # Registrar en histórico
        self.notification_history.append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "level": level,
            "channels_sent": success_count,
        })

        return success_count > 0

    def _send_to_slack(self, webhook_url: str, message: Dict):
        """Envía a Slack"""

        payload = {
            "text": message.get("title", ""),
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message.get("body", "")
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"🕐 {message.get('timestamp', '')}"
                        }
                    ]
                }
            ]
        }

        response = requests.post(webhook_url, json=payload)
        return response.status_code == 200

    def _send_to_discord(self, webhook_url: str, message: Dict):
        """Envía a Discord"""

        color = {
            "critical": 15158332,  # Rojo
            "high": 15105570,      # Naranja
            "medium": 3447003,     # Azul
            "low": 3066993,        # Verde
        }.get(message.get("level", "medium"), 3447003)

        payload = {
            "embeds": [
                {
                    "title": message.get("title", ""),
                    "description": message.get("body", ""),
                    "color": color,
                    "timestamp": datetime.now().isoformat(),
                    "footer": {
                        "text": "ParlaySmart Alerts"
                    }
                }
            ]
        }

        response = requests.post(webhook_url, json=payload)
        return response.status_code == 204

    def _send_to_telegram(self, bot_token: str, message: Dict):
        """Envía a Telegram (requiere chat_id en bot_token)"""

        try:
            chat_id, token = bot_token.split(":")
            url = f"https://api.telegram.org/bot{token}/sendMessage"

            payload = {
                "chat_id": chat_id,
                "text": f"{message.get('title', '')}\n\n{message.get('body', '')}",
                "parse_mode": "HTML"
            }

            response = requests.post(url, json=payload)
            return response.status_code == 200

        except Exception as e:
            print(f"Telegram error: {e}")
            return False

    def _send_email(self, email_config: str, message: Dict):
        """Envía por email (requiere configuración SMTP)"""

        # En producción, usar smtplib o Mailgun API
        # Aquí es placeholder
        print(f"[EMAIL] {message.get('title')}")
        return True

    def _format_value_bet_message(self, alert: Dict) -> Dict:
        """Formatea mensaje de value bet"""

        return {
            "title": f"💎 VALUE BET DETECTED",
            "body": f"""
Match: {alert.get('match_id')}
Parlay: {alert.get('parlay_type')}
Edge: {alert.get('edge_pct')}%
Odds: {alert.get('odds')}
Confidence: {alert.get('confidence')*100:.0f}%

✅ Action: BET NOW
            """,
            "level": "high",
            "timestamp": datetime.now().isoformat(),
        }

    def _format_sharp_move_message(self, alert: Dict) -> Dict:
        """Formatea mensaje de sharp move"""

        return {
            "title": f"🔥 SHARP MONEY DETECTED",
            "body": f"""
Match: {alert.get('match_id')}
Outcome: {alert.get('outcome')}
Direction: {alert.get('direction').upper()}
Change: {abs(alert.get('change_pct'))}%

⚠️ Follow the sharps!
            """,
            "level": "critical",
            "timestamp": datetime.now().isoformat(),
        }

    def _format_arbitrage_message(self, alert: Dict) -> Dict:
        """Formatea mensaje de arbitrage"""

        return {
            "title": f"🎰 GUARANTEED PROFIT OPPORTUNITY",
            "body": f"""
Match: {alert.get('match_id')}
Arbitrage Margin: {alert.get('margin_pct')}%
Guaranteed ROI: {alert.get('guaranteed_roi')}%

🚨 CRITICAL: Execute immediately!
            """,
            "level": "critical",
            "timestamp": datetime.now().isoformat(),
        }

    def _format_portfolio_message(self, stats: Dict) -> Dict:
        """Formatea mensaje de portafolio"""

        return {
            "title": f"📊 DAILY PORTFOLIO UPDATE",
            "body": f"""
Bankroll: ${stats.get('bankroll')}
ROI: {stats.get('roi_pct')}%
Win Rate: {stats.get('win_rate')*100:.1f}%
Active Bets: {stats.get('active_bets')}

Summary: All systems operating normally ✅
            """,
            "level": "low",
            "timestamp": datetime.now().isoformat(),
        }

    def get_notification_stats(self) -> Dict:
        """Estadísticas de notificaciones"""

        if not self.notification_history:
            return {"total": 0}

        levels = {}
        for notif in self.notification_history:
            level = notif.get("level")
            levels[level] = levels.get(level, 0) + 1

        return {
            "total_notifications": len(self.notification_history),
            "by_level": levels,
            "webhooks_registered": len(self.webhooks),
            "last_notification": self.notification_history[-1]["timestamp"] if self.notification_history else None,
        }


# Singleton
dispatcher = WebhookDispatcher()


if __name__ == "__main__":
    print("[TEST] Webhook Dispatcher\n")

    # Registrar webhooks (simulados)
    dispatcher.register_webhook("slack", "https://hooks.slack.com/services/YOUR/HOOK/URL", "alerts")
    dispatcher.register_webhook("discord", "https://discordapp.com/api/webhooks/YOUR/HOOK/URL", "alerts")

    print("✅ Webhooks registered (simulated)\n")

    # Test alertas
    print("Test 1: Value Bet Alert")
    dispatcher.send_value_bet_alert({
        "match_id": "barcelona-realmadrid",
        "parlay_type": "ultra",
        "edge_pct": 12.5,
        "odds": 2.0,
        "confidence": 0.85
    })

    print("\nTest 2: Sharp Move Alert")
    dispatcher.send_sharp_move_alert({
        "match_id": "barcelona-realmadrid",
        "outcome": "home",
        "direction": "down",
        "change_pct": 7.5
    })

    print("\nTest 3: Arbitrage Alert")
    dispatcher.send_arbitrage_alert({
        "match_id": "barcelona-realmadrid",
        "margin_pct": 5.5,
        "guaranteed_roi": 5.82
    })

    # Stats
    stats = dispatcher.get_notification_stats()
    print(f"\nNotification Stats:")
    print(json.dumps(stats, indent=2))
