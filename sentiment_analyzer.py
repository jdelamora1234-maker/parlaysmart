"""
SENTIMENT ANALYSIS ENGINE - Análisis de sentimiento en noticias
Fuentes: ESPN, Goal.com, Marca, AS
Beneficio: Detectar cambios de mood/confianza del equipo
Expectativa: +2-3% de edge temprano
"""

from typing import Dict, List, Tuple
import re
from datetime import datetime, timedelta

class SentimentAnalyzer:
    """Analiza sentimiento de noticias sobre equipos"""

    def __init__(self):
        self.sentiment_keywords = {
            # POSITIVO
            "positive": {
                "win": 1.0, "victory": 1.0, "defeated": 1.0,
                "excellent": 0.8, "great": 0.7, "amazing": 0.9,
                "comeback": 0.8, "dominant": 0.8, "inspired": 0.7,
                "crucial": 0.6, "confidence": 0.7, "momentum": 0.7,
                "unstoppable": 0.9, "brilliant": 0.8, "fantastic": 0.8,
            },
            # NEGATIVO
            "negative": {
                "loss": -1.0, "defeat": -1.0, "lost": -1.0,
                "poor": -0.7, "bad": -0.6, "terrible": -0.9,
                "collapse": -0.9, "crisis": -0.8, "disaster": -0.9,
                "injury": -0.5, "injured": -0.5, "suspended": -0.6,
                "struggling": -0.6, "crisis": -0.8, "nightmare": -0.9,
                "disastrous": -0.9, "shameful": -0.8,
            }
        }

        self.team_sentiment_history = {}

    def analyze_text(self, text: str) -> Dict[str, float]:
        """Analiza sentimiento de un texto"""

        text_lower = text.lower()

        positive_score = 0.0
        negative_score = 0.0

        for word, weight in self.sentiment_keywords["positive"].items():
            if word in text_lower:
                positive_score += weight

        for word, weight in self.sentiment_keywords["negative"].items():
            if word in text_lower:
                negative_score += weight

        # Normalizar
        total_score = positive_score + abs(negative_score)

        if total_score == 0:
            sentiment = 0.0
        else:
            sentiment = (positive_score - abs(negative_score)) / total_score

        return {
            "sentiment": round(sentiment, 3),  # -1.0 (muy negativo) a +1.0 (muy positivo)
            "positive_score": round(positive_score, 2),
            "negative_score": round(negative_score, 2),
            "magnitude": round(abs(sentiment), 3),
            "classification": (
                "VERY_POSITIVE" if sentiment > 0.7 else
                "POSITIVE" if sentiment > 0.3 else
                "NEUTRAL" if -0.3 <= sentiment <= 0.3 else
                "NEGATIVE" if sentiment > -0.7 else
                "VERY_NEGATIVE"
            )
        }

    def analyze_news_feed(self,
                         team: str,
                         news_items: List[Dict]) -> Dict:
        """
        Analiza múltiples noticias sobre un equipo

        news_items: [
            {"title": "...", "body": "...", "timestamp": "2026-06-24T10:00:00"},
            ...
        ]
        """

        if not news_items:
            return {"error": "No news items"}

        sentiments = []
        recent_news = []

        for item in news_items:
            title = item.get("title", "")
            body = item.get("body", "")
            timestamp = item.get("timestamp", datetime.now().isoformat())

            full_text = f"{title} {body}"

            sentiment = self.analyze_text(full_text)

            sentiments.append(sentiment["sentiment"])

            recent_news.append({
                "title": title,
                "sentiment": sentiment["sentiment"],
                "classification": sentiment["classification"],
                "timestamp": timestamp,
            })

        # Calcular promedio
        avg_sentiment = sum(sentiments) / len(sentiments)

        # Trend: comparar últimas 3 noticias vs anteriores
        recent_avg = sum(sentiments[-3:]) / min(3, len(sentiments)) if sentiments else 0
        older_avg = sum(sentiments[:-3]) / max(1, len(sentiments) - 3) if len(sentiments) > 3 else 0

        trend = recent_avg - older_avg

        return {
            "team": team,
            "average_sentiment": round(avg_sentiment, 3),
            "sentiment_trend": round(trend, 3),  # + = improving, - = deteriorating
            "recent_news": recent_news,
            "impact_on_odds": round(avg_sentiment * 0.05, 3),  # -5% a +5% impact
            "recommendation": (
                "BULLISH" if avg_sentiment > 0.5 else
                "SLIGHTLY_BULLISH" if avg_sentiment > 0.1 else
                "NEUTRAL" if -0.1 <= avg_sentiment <= 0.1 else
                "SLIGHTLY_BEARISH" if avg_sentiment > -0.5 else
                "BEARISH"
            )
        }

    def detect_sentiment_anomaly(self,
                                team: str,
                                current_sentiment: float,
                                historical_avg: float = 0.0) -> Dict:
        """
        Detecta cambios anómalos en sentimiento

        Útil para detectar "shock news" que movimiento de línea
        """

        deviation = current_sentiment - historical_avg
        std_deviation = abs(deviation) / max(0.1, abs(historical_avg))

        return {
            "team": team,
            "current_sentiment": round(current_sentiment, 3),
            "historical_avg": round(historical_avg, 3),
            "deviation": round(deviation, 3),
            "std_deviations": round(std_deviation, 2),
            "is_anomaly": std_deviation > 2.0,  # > 2 SD = significant change
            "anomaly_severity": (
                "CRITICAL" if std_deviation > 3.0 else
                "HIGH" if std_deviation > 2.5 else
                "MODERATE" if std_deviation > 2.0 else
                "NORMAL"
            ),
            "market_impact_expected": round(std_deviation * 0.03, 3),  # Estimated line movement
        }

    def sentiment_momentum(self,
                          team: str,
                          sentiment_history: List[float]) -> Dict:
        """
        Calcula momentum del sentimiento

        sentiment_history: últimos sentimientos ordenados cronológicamente
        """

        if len(sentiment_history) < 2:
            return {"error": "Need at least 2 data points"}

        # Calcular tasa de cambio
        recent = sentiment_history[-3:]  # Últimos 3
        older = sentiment_history[:3] if len(sentiment_history) >= 3 else sentiment_history

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        momentum = recent_avg - older_avg

        # Acceleration
        if len(sentiment_history) >= 4:
            very_recent = sentiment_history[-1]
            older_point = sentiment_history[-4]
            acceleration = (very_recent - recent_avg) - (older_avg - older_point)
        else:
            acceleration = 0

        return {
            "team": team,
            "current_sentiment": round(sentiment_history[-1], 3),
            "momentum": round(momentum, 3),  # + = improving, - = declining
            "acceleration": round(acceleration, 3),  # How fast is it changing
            "strength": (
                "STRONG" if abs(momentum) > 0.3 else
                "MODERATE" if abs(momentum) > 0.15 else
                "WEAK"
            ),
            "direction": "IMPROVING" if momentum > 0 else "DECLINING",
            "forecast_next_period": round(sentiment_history[-1] + momentum, 3),
        }

    def get_team_sentiment_report(self, team: str) -> Dict:
        """Reporte completo de sentimiento para un equipo"""

        if team not in self.team_sentiment_history:
            return {"error": f"No data for {team}"}

        history = self.team_sentiment_history[team]

        return {
            "team": team,
            "current_sentiment": round(history[-1] if history else 0, 3),
            "7day_average": round(sum(history[-7:]) / min(7, len(history)), 3),
            "30day_average": round(sum(history[-30:]) / min(30, len(history)), 3),
            "momentum": self.sentiment_momentum(team, history),
            "recommendation": "MONITOR_CLOSELY" if len(history) > 0 and abs(history[-1]) > 0.5 else "NEUTRAL",
        }


# Singleton
sentiment_analyzer = SentimentAnalyzer()


if __name__ == "__main__":
    print("[TEST] Sentiment Analyzer\n")

    # Test sentiment analysis
    text1 = "Incredible win! Amazing performance, dominant display. Team is unstoppable!"
    sentiment1 = sentiment_analyzer.analyze_text(text1)
    print(f"Positive text: {sentiment1['classification']}, sentiment: {sentiment1['sentiment']}\n")

    text2 = "Disaster! Terrible loss. Team is struggling, poor defense, shameful display."
    sentiment2 = sentiment_analyzer.analyze_text(text2)
    print(f"Negative text: {sentiment2['classification']}, sentiment: {sentiment2['sentiment']}\n")

    # Analyze news feed
    news = [
        {"title": "Team wins 3-0", "body": "Dominant performance", "timestamp": "2026-06-24T10:00:00"},
        {"title": "Star player injured", "body": "Out for 2 weeks", "timestamp": "2026-06-24T11:00:00"},
    ]

    report = sentiment_analyzer.analyze_news_feed("Barcelona", news)
    print(f"Team sentiment: {report['average_sentiment']}, Recommendation: {report['recommendation']}")
