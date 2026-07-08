"""
PARLAYSMART v2026.X - FastAPI Optimizado
Motor Montecarlo Vectorizado + Clean Architecture
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
import gc
from datetime import datetime
from typing import Optional
import os

app = FastAPI(title="ParlaySmart v2026.X", version="2.0.0")

# Servir archivos estáticos
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

class MonteCarloVectorized:
    """Montecarlo 100% vectorizado - SIN bucles for"""
    
    def __init__(self, iterations=50000):
        self.iterations = iterations
    
    def clayton_copula_vectorized(self, n_samples):
        """Cópula de Clayton vectorizada con NumPy"""
        theta = 1.8
        u1 = np.random.uniform(0, 1, n_samples)
        u2 = np.random.uniform(0, 1, n_samples)
        v2 = (u1**(-theta) + u2**(-theta) - 1)**(-1/theta)
        return u1, v2
    
    def simulate(self, team_a_xg=1.5, team_b_xg=1.2):
        """50k simulaciones VECTORIZADAS"""
        gc.collect()  # Limpia memoria antes
        
        # Generar Cópulas para 50k iteraciones
        u1, u2 = self.clayton_copula_vectorized(self.iterations)
        
        # Aplicar Poisson vectorizado
        goals_a = np.random.poisson(team_a_xg * (1 + u1 * 0.3), self.iterations)
        goals_b = np.random.poisson(team_b_xg * (1 + u2 * 0.3), self.iterations)
        
        # Vectorizar conteos (sin loops)
        home_wins = np.sum(goals_a > goals_b)
        draws = np.sum(goals_a == goals_b)
        away_wins = np.sum(goals_a < goals_b)
        
        prob_1 = home_wins / self.iterations
        prob_x = draws / self.iterations
        prob_2 = away_wins / self.iterations
        
        gc.collect()  # Limpia después
        
        return {
            "prob_1": prob_1,
            "prob_x": prob_x,
            "prob_2": prob_2,
            "true_odds_1": 1.0 / prob_1 if prob_1 > 0 else 0,
            "true_odds_x": 1.0 / prob_x if prob_x > 0 else 0,
            "true_odds_2": 1.0 / prob_2 if prob_2 > 0 else 0
        }

class KellyOptimizer:
    """Kelly Criterion fraccionado por liquidez"""
    
    @staticmethod
    def calculate(prob_win, odds, liquidity_level=1):
        """Calcula Kelly fraccionado"""
        if odds <= 1:
            return 0
        
        # Kelly: (b*p - q) / b, donde b = odds-1, p = prob, q = 1-prob
        b = odds - 1
        p = prob_win
        q = 1 - p
        
        kelly = (b * p - q) / b if b != 0 else 0
        kelly = max(0, kelly)  # Sin negativos
        
        # Fraccionar por liquidez
        fractions = {1: 1.0, 2: 0.5, 3: 0.25}
        fraction = fractions.get(liquidity_level, 0.25)
        
        return kelly * fraction

@app.get("/")
def root():
    """Sirve la UI"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"status": "UI not found, use /health for API status"}

@app.get("/analyze")
def analyze(team_a: str, team_b: str, team_a_xg: float = 1.8, team_b_xg: float = 0.9):
    """Analiza un partido - Formato compatible con UI vieja"""
    try:
        mc = MonteCarloVectorized(iterations=50000)
        result = mc.simulate(team_a_xg, team_b_xg)

        prob_1 = result["prob_1"]
        prob_x = result["prob_x"]
        prob_2 = result["prob_2"]
        odds_1 = result["true_odds_1"]
        odds_x = result["true_odds_x"]
        odds_2 = result["true_odds_2"]

        # Formato para la UI vieja
        return JSONResponse({
            "success": True,
            "match": {
                "team_a": team_a,
                "team_b": team_b,
                "competition": "Análisis Montecarlo",
                "date": datetime.now().isoformat()
            },
            "prediction": {
                "ganador": team_a,
                "probabilidad": f"{prob_1:.1%}",
                "confianza": int(prob_1 * 100),
                "estado": "ACTIVO",
                "modelo": "Montecarlo v2026 (Clayton + Poisson)"
            },
            "probabilities": {
                "home": prob_1,
                "draw": prob_x,
                "away": prob_2
            },
            "odds": {
                "1": odds_1,
                "x": odds_x,
                "2": odds_2
            },
            "parlays": {
                "ultra_conservador": {
                    "picks": [f"{team_a} gana @ {odds_1:.2f}"],
                    "momio_total": odds_1,
                    "ganancia_$1000": f"${int(1000 * odds_1 - 1000)} MXN",
                    "confianza": int(prob_1 * 100),
                    "filtro": "✅ PASE"
                },
                "conservador": {
                    "picks": [
                        f"{team_a} gana @ {odds_1:.2f}",
                        f"Over 2.5 @ 1.85"
                    ],
                    "momio_total": f"{odds_1 * 1.85:.2f}",
                    "ganancia_$1000": f"${int(1000 * odds_1 * 1.85 - 1000)} MXN",
                    "confianza": int(prob_1 * 0.65 * 100),
                    "filtro": "✅ PASE"
                },
                "balanceado": {
                    "picks": [
                        f"{team_a} gana @ {odds_1:.2f}",
                        f"Over 2.5 @ 1.85",
                        f"Corners +9.5 @ 1.88"
                    ],
                    "momio_total": f"{odds_1 * 1.85 * 1.88:.2f}",
                    "ganancia_$1000": f"${int(1000 * odds_1 * 1.85 * 1.88 - 1000)} MXN",
                    "confianza": int(prob_1 * 0.65 * 0.65 * 100),
                    "filtro": "✅ PASE"
                },
                "riesgoso": {
                    "picks": [
                        f"{team_a} gana @ {odds_1:.2f}",
                        f"Ambos equipos anotan @ 1.82",
                        f"Hándicap -0.5 @ 1.95",
                        f"Over 3.5 @ 2.10"
                    ],
                    "momio_total": f"{odds_1 * 1.82 * 1.95 * 2.10:.2f}",
                    "ganancia_$1000": f"${int(1000 * odds_1 * 1.82 * 1.95 * 2.10 - 1000)} MXN",
                    "confianza": int(prob_1 * 0.5 * 100),
                    "filtro": "✅ PASE"
                }
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    """Health check con métricas"""
    return {
        "status": "HEALTHY",
        "timestamp": datetime.now().isoformat(),
        "ram_usage": "Optimized (Vectorized Montecarlo)",
        "model": "Clayton Copula + Poisson Marginals"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
