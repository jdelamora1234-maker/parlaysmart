"""
Búsqueda robusta de información en Google.
Sistema de fallback: Gemini → SerpAPI → DuckDuckGo → datos locales
"""

import requests
import json
import os
from datetime import datetime

def search_google_robust(query, max_retries=2):
    """
    Busca información en Google usando múltiples métodos.
    GARANTIZA devolver datos (nunca vacío).
    """

    print(f"[SEARCH] Buscando: {query}")

    # Método 1: SerpAPI (más confiable)
    result = _search_serpapi(query)
    if result:
        print("[SEARCH] ✅ Datos obtenidos via SerpAPI")
        return result

    # Método 2: DuckDuckGo API (gratuito)
    result = _search_duckduckgo(query)
    if result:
        print("[SEARCH] ✅ Datos obtenidos via DuckDuckGo")
        return result

    # Método 3: Datos de fallback local
    print("[SEARCH] ⚠️ Usando datos de fallback local")
    return _get_fallback_data(query)


def _search_serpapi(query):
    """Busca usando SerpAPI (requiere API key)"""
    try:
        api_key = os.environ.get("SERPAPI_KEY", "").strip()
        if not api_key:
            print("[SERPAPI] No configurado")
            return None

        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": api_key,
            "engine": "google",
            "num": 5
        }

        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("organic_results", [])
            if results:
                return {
                    "source": "SerpAPI",
                    "query": query,
                    "results": [
                        {
                            "title": r.get("title", ""),
                            "link": r.get("link", ""),
                            "snippet": r.get("snippet", "")
                        }
                        for r in results[:5]
                    ],
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        print(f"[SERPAPI] Error: {e}")

    return None


def _search_duckduckgo(query):
    """Busca usando DuckDuckGo API (gratuito)"""
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }

        resp = requests.get(url, params=params, timeout=10, headers={
            "User-Agent": "ParlaySmart/1.0"
        })

        if resp.status_code == 200:
            data = resp.json()
            results = data.get("Results", [])

            if results:
                return {
                    "source": "DuckDuckGo",
                    "query": query,
                    "results": [
                        {
                            "title": r.get("Text", ""),
                            "link": r.get("FirstURL", ""),
                            "snippet": r.get("Result", "")
                        }
                        for r in results[:5]
                    ],
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        print(f"[DUCKDUCKGO] Error: {e}")

    return None


def _get_fallback_data(query):
    """Devuelve datos de fallback local"""
    return {
        "source": "fallback_local",
        "query": query,
        "results": [
            {
                "title": "Información local",
                "link": "local",
                "snippet": f"Búsqueda local para: {query}"
            }
        ],
        "timestamp": datetime.now().isoformat(),
        "note": "Sin acceso a búsqueda en línea. Usando análisis local."
    }


def get_team_info(team_name):
    """Obtiene información de un equipo buscando en Google"""
    query = f"{team_name} fútbol stats últimos resultados"
    return search_google_robust(query)


def get_player_injuries(team_name):
    """Obtiene información de lesiones de un equipo"""
    query = f"{team_name} jugadores lesionados ausentes 2026"
    return search_google_robust(query)


def get_match_info(team_a, team_b):
    """Obtiene información de un partido específico"""
    query = f"{team_a} vs {team_b} predicción análisis"
    return search_google_robust(query)


if __name__ == "__main__":
    # Test
    result = search_google_robust("Argentina vs Brasil fútbol 2026")
    print(json.dumps(result, indent=2, ensure_ascii=False))
