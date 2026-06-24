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
    """Devuelve datos de fallback local con contexto mejorado"""
    return {
        "source": "fallback_local",
        "query": query,
        "results": [
            {
                "title": "Análisis sin búsqueda en línea (Gemini usará Google Search)",
                "link": "local",
                "snippet": f"Gemini analizará {query} usando sus herramientas de búsqueda integradas. Para mejor precisión, configura SERPAPI_KEY en Render."
            }
        ],
        "timestamp": datetime.now().isoformat(),
        "note": "⚠️ Usando análisis de Gemini + Google Search integrado (no SerpAPI)"
    }


def get_team_info(team_name):
    """Obtiene información de un equipo - BÚSQUEDAS SEGMENTADAS"""
    print(f"[SEARCH] Buscando información segmentada de {team_name}")

    searches = {
        "stats_recent": search_google_robust(f"{team_name} últimos 5 partidos 2026 goles xG estadísticas"),
        "advanced_stats": search_google_robust(f"{team_name} xA big chances PPDA 2026 fútbol avanzado"),
        "form": search_google_robust(f"{team_name} racha actual forma últimas 10 partidos"),
        "possession": search_google_robust(f"{team_name} posesión promedio tiki taka 2026"),
        "defense": search_google_robust(f"{team_name} defensa goles concedidos xGA prevención")
    }

    return searches


def get_player_injuries(team_name):
    """Obtiene información de lesiones - BÚSQUEDAS ESPECÍFICAS"""
    print(f"[SEARCH] Buscando lesiones de {team_name}")

    searches = {
        "injuries": search_google_robust(f"{team_name} jugadores lesionados ausentes 2026"),
        "key_players": search_google_robust(f"{team_name} jugadores clave estrellas 2026 goles asists"),
        "suspensions": search_google_robust(f"{team_name} sanciones tarjetas suspensiones 2026"),
        "fatigue": search_google_robust(f"{team_name} fatiga cansancio partidos últimos 21 días")
    }

    return searches


def get_match_info(team_a, team_b):
    """Obtiene información de un partido - BÚSQUEDAS EXHAUSTIVAS × 10"""
    print(f"[SEARCH] Buscando información completa: {team_a} vs {team_b}")

    searches = {
        "h2h": search_google_robust(f"{team_a} vs {team_b} historial h2h últimos 10 años"),
        "tactics_a": search_google_robust(f"{team_a} alineación formación táctica 2026"),
        "tactics_b": search_google_robust(f"{team_b} alineación formación táctica 2026"),
        "referee": search_google_robust(f"árbitro {team_a} vs {team_b} tarjetas corners 2026"),
        "stadium": search_google_robust(f"estadio {team_a} clima temperatura humedad"),
        "news": search_google_robust(f"{team_a} {team_b} noticias últimas 48 horas 2026"),
        "psychology": search_google_robust(f"{team_a} vestuario motivación moral 2026"),
        "market": search_google_robust(f"{team_a} vs {team_b} momios apuestas inteligente"),
        "travel": search_google_robust(f"{team_b} viaje {team_a} km jet lag distancia"),
        "context": search_google_robust(f"{team_a} vs {team_b} importancia torneo ranking")
    }

    return searches


if __name__ == "__main__":
    # Test
    result = search_google_robust("Argentina vs Brasil fútbol 2026")
    print(json.dumps(result, indent=2, ensure_ascii=False))
