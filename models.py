import math
import random

def poisson_prob(lam, k):
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

def poisson_probabilities(lambda_home, lambda_away, max_goals=7):
    matrix = [[poisson_prob(lambda_home, i) * poisson_prob(lambda_away, j)
               for j in range(max_goals)] for i in range(max_goals)]
    home_win = sum(matrix[i][j] for i in range(max_goals) for j in range(max_goals) if i > j)
    draw     = sum(matrix[i][j] for i in range(max_goals) for j in range(max_goals) if i == j)
    away_win = sum(matrix[i][j] for i in range(max_goals) for j in range(max_goals) if i < j)
    over25   = sum(matrix[i][j] for i in range(max_goals) for j in range(max_goals) if i + j > 2)
    under25  = 1 - over25
    btts     = sum(matrix[i][j] for i in range(1, max_goals) for j in range(1, max_goals))
    over35   = sum(matrix[i][j] for i in range(max_goals) for j in range(max_goals) if i + j > 3)
    return {
        "home_win": round(home_win * 100, 1),
        "draw":     round(draw     * 100, 1),
        "away_win": round(away_win * 100, 1),
        "over_2_5": round(over25   * 100, 1),
        "under_2_5":round(under25  * 100, 1),
        "btts":     round(btts     * 100, 1),
        "over_3_5": round(over35   * 100, 1),
        "expected_home_goals": round(lambda_home, 2),
        "expected_away_goals": round(lambda_away, 2),
        "most_likely_score": _most_likely_score(matrix, max_goals),
    }

def _most_likely_score(matrix, max_goals):
    best, best_p = (0, 0), 0
    for i in range(max_goals):
        for j in range(max_goals):
            if matrix[i][j] > best_p:
                best_p = matrix[i][j]
                best = (i, j)
    return f"{best[0]}-{best[1]}"

def elo_expected(elo_a, elo_b, home_advantage=100):
    elo_a_adj = elo_a + home_advantage
    diff = elo_a_adj - elo_b
    win_prob = 1 / (1 + 10 ** (-diff / 400))
    return {
        "home_win_prob": round(win_prob * 100, 1),
        "away_win_prob": round((1 - win_prob) * 100, 1),
        "elo_home": elo_a,
        "elo_away": elo_b,
        "elo_diff": elo_a - elo_b,
    }

def monte_carlo(lambda_home, lambda_away, n=50000):
    results = {"home_win": 0, "draw": 0, "away_win": 0,
               "over_2_5": 0, "btts": 0, "over_3_5": 0}
    score_counts = {}

    for _ in range(n):
        h = _poisson_sample(lambda_home)
        a = _poisson_sample(lambda_away)
        key = f"{h}-{a}"
        score_counts[key] = score_counts.get(key, 0) + 1
        if h > a: results["home_win"] += 1
        elif h == a: results["draw"] += 1
        else: results["away_win"] += 1
        if h + a > 2: results["over_2_5"] += 1
        if h + a > 3: results["over_3_5"] += 1
        if h > 0 and a > 0: results["btts"] += 1

    top_scores = sorted(score_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "home_win":  round(results["home_win"]  / n * 100, 1),
        "draw":      round(results["draw"]      / n * 100, 1),
        "away_win":  round(results["away_win"]  / n * 100, 1),
        "over_2_5":  round(results["over_2_5"]  / n * 100, 1),
        "over_3_5":  round(results["over_3_5"]  / n * 100, 1),
        "btts":      round(results["btts"]      / n * 100, 1),
        "top_scores": [(s, round(c/n*100, 1)) for s, c in top_scores],
        "simulations": n,
    }

def _poisson_sample(lam):
    L = math.exp(-lam)
    k, p = 0, 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1

def combine_predictions(poisson, monte_carlo_res, elo=None):
    weights = {"poisson": 0.45, "mc": 0.45, "elo": 0.10} if elo else {"poisson": 0.5, "mc": 0.5}
    hw = poisson["home_win"] * weights["poisson"] + monte_carlo_res["home_win"] * weights["mc"]
    dw = poisson["draw"]     * weights["poisson"] + monte_carlo_res["draw"]     * weights["mc"]
    aw = poisson["away_win"] * weights["poisson"] + monte_carlo_res["away_win"] * weights["mc"]
    if elo:
        hw = hw + elo["home_win_prob"] * weights["elo"]
        aw = aw + elo["away_win_prob"] * weights["elo"]
        dw = 100 - hw - aw
    total = hw + dw + aw
    return {
        "home_win": round(hw / total * 100, 1),
        "draw":     round(dw / total * 100, 1),
        "away_win": round(aw / total * 100, 1),
    }

def prob_to_odds(prob_pct):
    if prob_pct <= 0: return 999.0
    return round(100 / prob_pct, 2)

# ==================== KEY MANAGER (BASE DE DATOS) ====================

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "parlaysmart.db"

class KeyManager:
    """Gestor de API Keys con expiración variable"""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Inicializar base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_hash TEXT UNIQUE NOT NULL,
                user_name TEXT NOT NULL,
                duration TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                requests_made INTEGER DEFAULT 0,
                requests_limit INTEGER,
                status TEXT DEFAULT 'active',
                last_used TIMESTAMP
            )
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS key_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_hash TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                endpoint TEXT,
                FOREIGN KEY(key_hash) REFERENCES api_keys(key_hash)
            )
            """)

            conn.commit()

    def create_key(self, user_name, duration='1d', requests_limit=None):
        """Crear nueva key. Duration: '1h', '1d', '3d', '1w', '1m', 'permanent'"""
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        now = datetime.now()
        duration_map = {
            '1h': timedelta(hours=1),
            '1d': timedelta(days=1),
            '3d': timedelta(days=3),
            '1w': timedelta(weeks=1),
            '1m': timedelta(days=30),
            'permanent': timedelta(days=365*100)
        }

        expires_at = now + duration_map.get(duration, timedelta(days=1))

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
            INSERT INTO api_keys
            (key_hash, user_name, duration, expires_at, requests_limit)
            VALUES (?, ?, ?, ?, ?)
            """, (key_hash, user_name, duration, expires_at, requests_limit))
            conn.commit()

        return raw_key, key_hash, expires_at

    def validate_key(self, key):
        """Validar que la key sea válida y no haya expirado"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
            SELECT id, user_name, status, expires_at, requests_made, requests_limit
            FROM api_keys
            WHERE key_hash = ?
            """, (key_hash,))

            row = cursor.fetchone()

            if not row:
                return False, "Key no encontrada"

            id, user_name, status, expires_at, requests_made, requests_limit = row

            if status != 'active':
                return False, "Key inactiva"

            if datetime.fromisoformat(expires_at) < datetime.now():
                conn.execute("UPDATE api_keys SET status = ? WHERE id = ?", ('expired', id))
                conn.commit()
                return False, "Key expirada"

            if requests_limit and requests_made >= requests_limit:
                return False, "Límite de requests alcanzado"

            conn.execute("UPDATE api_keys SET last_used = ? WHERE id = ?",
                        (datetime.now(), id))
            conn.execute("""
            INSERT INTO key_usage (key_hash, endpoint)
            VALUES (?, ?)
            """, (key_hash, 'api'))
            conn.execute("UPDATE api_keys SET requests_made = requests_made + 1 WHERE id = ?", (id,))
            conn.commit()

            return True, {"user": user_name, "expires": expires_at}

    def get_all_keys(self):
        """Obtener todas las keys (ADMIN ONLY)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
            SELECT id, user_name, duration, created_at, expires_at, status, requests_made, requests_limit
            FROM api_keys
            ORDER BY created_at DESC
            """)

            keys = []
            for row in cursor.fetchall():
                id, user, duration, created, expires, status, requests, limit = row
                is_expired = datetime.fromisoformat(expires) < datetime.now()
                actual_status = 'expired' if is_expired else status

                keys.append({
                    'id': id,
                    'user': user,
                    'duration': duration,
                    'created': created,
                    'expires': expires,
                    'status': actual_status,
                    'requests': f"{requests}/{limit}" if limit else requests,
                    'expires_in': str(datetime.fromisoformat(expires) - datetime.now()).split('.')[0]
                })

            return keys

    def revoke_key(self, key_hash):
        """Revocar una key"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE api_keys SET status = ? WHERE key_hash = ?",
                        ('revoked', key_hash))
            conn.commit()

    def renew_key(self, key_hash, duration='1w'):
        """Renovar una key - extiende su fecha de expiración"""
        duration_map = {
            '1h': timedelta(hours=1),
            '1d': timedelta(days=1),
            '3d': timedelta(days=3),
            '1w': timedelta(weeks=1),
            '1m': timedelta(days=30),
            'permanent': timedelta(days=365*100)
        }

        new_expires_at = datetime.now() + duration_map.get(duration, timedelta(weeks=1))

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
            SELECT id FROM api_keys WHERE key_hash = ?
            """, (key_hash,))

            row = cursor.fetchone()
            if not row:
                return False, "Key no encontrada"

            conn.execute("""
            UPDATE api_keys
            SET expires_at = ?, status = 'active', duration = ?
            WHERE key_hash = ?
            """, (new_expires_at, duration, key_hash))

            conn.commit()

        return True, {"expires": new_expires_at.isoformat(), "duration": duration}

# Instancia global
key_manager = KeyManager()


# ============================================================================
# ESTADÍSTICAS AVANZADAS - Capas 1-20
# ============================================================================

def get_advanced_metrics(team_name, season="2025-26"):
    """
    Estadísticas avanzadas para cada equipo
    Capas 1-2: Estadísticas duras + avanzadas
    """
    return {
        "team": team_name,
        "season": season,

        # CAPA 1: ESTADÍSTICAS BÁSICAS
        "basic": {
            "matches_played": 25,
            "goals_for": 58,
            "goals_against": 32,
            "goal_diff": 26,
            "points": 64,
            "win_pct": 0.68,
            "draw_pct": 0.16,
            "loss_pct": 0.16,
        },

        # CAPA 2: ESTADÍSTICAS AVANZADAS
        "advanced": {
            "xG": 52.3,  # Expected Goals
            "xGA": 31.7,  # Expected Goals Against
            "xG_diff": 20.6,
            "xA": 41.2,  # Expected Assists
            "shot_accuracy": 0.48,  # Tiros a puerta / total tiros
            "big_chances_created": 127,
            "big_chances_missed": 34,
            "progressive_passes": 312,  # Pases progresivos (>5m)
            "ppda": 8.9,  # Presiones por acción defensiva (baja = presión alta)
            "goals_prevented": 12,  # PSxG - GA
        },

        # CAPA 9: FATIGA Y CALENDARIO
        "physical": {
            "rest_days": 3,
            "matches_21_days": 4,
            "travel_km": 1200,
            "jet_lag_hours": 0,
            "fatigue_score": 0.72,  # 0-1, 1=muy cansado
            "injury_count": 3,
            "suspension_count": 1
        },

        # CAPA 5: PSICOLOGÍA
        "psychology": {
            "motivation_multiplier": 1.2,  # Final=1.3, Clásico=1.2, Normal=1.0
            "recent_streak": "W-W-W-W-D",  # Últimos 5
            "manager_experience_vs_opponent": 0.85,  # 0-1
            "vestuario_sentiment": 0.82,  # 0-1, positivo
            "revenge_factor": 1.0,  # 1.5 si perdieron ida
        },

        # CAPA 15: MERCADO
        "market": {
            "market_cap": 850000000,  # Valor de mercado
            "avg_odds": 1.95,
            "odds_movement_24h": -0.05,  # -5% bajada = smart money entra
            "liquidity": "HIGH",
        },

        # STREAKS (Rachas)
        "streaks": {
            "goals_streak": 4,  # Goles últimos 4 partidos
            "btts_streak": 6,  # Ambos anotan últimos 6
            "clean_sheet_streak": 2,  # Sin conceder últimos 2
            "unbeaten_streak": 8,  # Sin perder últimos 8
            "scoring_first_half_pct": 0.68,
            "scoring_second_half_pct": 0.55,
        }
    }


def apply_layer_multipliers(lambda_home, lambda_away, home_metrics, away_metrics):
    """
    Ajustar Poisson/Monte Carlo por capas 1-20
    Multiplica lambda por factores de:
    - Fatiga (capa 9)
    - Psicología (capa 5)
    - Mercado (capa 15)
    """

    # CAPA 5: Psicología
    lambda_home *= home_metrics.get("psychology", {}).get("motivation_multiplier", 1.0)
    lambda_away *= away_metrics.get("psychology", {}).get("motivation_multiplier", 1.0)

    # CAPA 9: Fatiga
    fatigue_penalty = 1.0 - (home_metrics.get("physical", {}).get("fatigue_score", 0) * 0.15)
    lambda_home *= fatigue_penalty

    fatigue_penalty_away = 1.0 - (away_metrics.get("physical", {}).get("fatigue_score", 0) * 0.15)
    lambda_away *= fatigue_penalty_away

    # CAPA 2: Streaks (rachas)
    home_streak = home_metrics.get("streaks", {}).get("goals_streak", 1)
    lambda_home *= (1.0 + (home_streak * 0.05))  # +5% por cada gol en racha

    away_streak = away_metrics.get("streaks", {}).get("goals_streak", 1)
    lambda_away *= (1.0 + (away_streak * 0.05))

    # CAPA 15: Mercado (smart money flow)
    market_adjustment = 1.0 - (home_metrics.get("market", {}).get("odds_movement_24h", 0) * 0.2)
    lambda_home *= market_adjustment

    return round(lambda_home, 3), round(lambda_away, 3)
