import os, json, re, hashlib, requests
from datetime import date as dt_date
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import poisson_probabilities, monte_carlo, combine_predictions, elo_expected, prob_to_odds, get_advanced_metrics, apply_layer_multipliers
from prompts import SYSTEM_PROMPT, build_analysis_prompt, build_today_matches_prompt, build_multi_analysis_prompt, build_single_parlay_prompt
from football_api import get_context_for_match, get_fixtures_for_mx_date, fixtures_to_matches
from data_sources import data_sources
from tracking import tracker
from ml_weights import optimizer

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "").strip()

# Validar que GEMINI_API_KEY esté configurada
if not GEMINI_API_KEY:
    print("❌ ERROR CRÍTICO: GEMINI_API_KEY no está configurada")
    print("   Debe estar en Render Dashboard → Settings → Environment Variables")
    # No fallar aquí, solo avisar. El error ocurrirá cuando se intente usar

def _get_real_odds(team_a, team_b):
    """Obtiene momios reales de The Odds API para un partido."""
    try:
        if not ODDS_API_KEY:
            return ""

        # Buscar el partido en The Odds API
        url = "https://api.the-odds-api.com/v4/sports/soccer_international/events"
        params = {
            "apiKey": ODDS_API_KEY,
            "limit": 500
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return ""

        data = r.json()
        events = data.get("data", [])

        # Buscar partido con nombres similares
        a_lower = team_a.lower().strip()
        b_lower = team_b.lower().strip()

        for event in events:
            home = event.get("home_team", "").lower()
            away = event.get("away_team", "").lower()

            # Búsqueda flexible de nombres
            if (a_lower in home or home in a_lower or a_lower in away or away in a_lower) and \
               (b_lower in home or home in b_lower or b_lower in away or away in b_lower):

                # Obtener momios del partido
                bookmakers = event.get("bookmakers", [])
                odds_info = f"\n=== MOMIOS REALES DE THE ODDS API ===\n"
                odds_info += f"Partido: {event.get('home_team')} vs {event.get('away_team')}\n"
                odds_info += f"Hora: {event.get('commence_time', 'N/A')}\n\n"

                for bm in bookmakers[:3]:  # Top 3 casas
                    bm_name = bm.get("title", "")
                    markets = bm.get("markets", [])
                    odds_info += f"{bm_name}:\n"

                    for market in markets:
                        if market.get("key") == "h2h":
                            outcomes = market.get("outcomes", [])
                            for outcome in outcomes:
                                odds_info += f"  {outcome.get('name')}: {outcome.get('price')}\n"
                    odds_info += "\n"

                return odds_info

        return ""
    except Exception:
        return ""

def _call_gemini(prompt, max_tokens=8000, retry=2):
    """Llamada a Gemini API usando Google Cloud REST API con fallback a modelos alternativos."""
    import time

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY no está configurada")

    # Probar modelos en orden de disponibilidad y estabilidad (Junio 2025)
    # gemini-2.0-flash es más estable que 2.5-flash que está muy sobrecargado
    models_to_try = ["gemini-2.0-flash", "gemini-2.0-flash-001", "gemini-2.5-flash", "gemini-2.5-pro"]

    for model_choice in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_choice}:generateContent?key={gemini_key}"

        for attempt in range(retry):
            try:
                payload = {
                    "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}]}],
                    "generationConfig": {
                        "maxOutputTokens": min(max_tokens, 8000),
                        "temperature": 0.3,
                    },
                    "tools": [{"googleSearch": {}}]
                }

                resp = requests.post(url, json=payload, timeout=60)  # Increased from 45 to 60 seconds

                if resp.status_code != 200:
                    error_body = resp.text[:500]
                    print(f"[Gemini] HTTP {resp.status_code}: {error_body}")
                    # Si es 503, intentar siguiente modelo
                    if resp.status_code == 503:
                        raise ValueError(f"Model overload (503): {model_choice}")
                    raise ValueError(f"HTTP {resp.status_code}: {error_body}")

                try:
                    data = resp.json()
                except Exception as json_err:
                    print(f"[Gemini] JSON parse error: {resp.text[:300]}")
                    raise ValueError(f"JSON parse error")

                # Validar estructura de respuesta Gemini
                candidates = data.get("candidates", [])
                if not candidates:
                    raise ValueError("No candidates")

                candidate = candidates[0]
                content = candidate.get("content", {})
                parts = content.get("parts", [])

                if not parts:
                    raise ValueError("No parts")

                text = parts[0].get("text", "").strip()

                if not text:
                    raise ValueError("Empty text")

                print(f"✅ {model_choice} SUCCESS")
                return text

            except Exception as e:
                error_msg = str(e)[:100]
                print(f"[{model_choice} attempt {attempt+1}/{retry}] ERROR: {error_msg}")
                if attempt == retry - 1:
                    # Pasar al siguiente modelo
                    break
                # Esperar antes de reintentar
                wait_time = 5 if "503" in error_msg else 2
                time.sleep(wait_time)

    raise ValueError("Gemini: Todos los modelos agotados o sobrecargados")

def validate_parlay_correlation(picks):
    """Valida que los picks no sean contradictorios"""
    contradictions = {
        ("gana_local", "gana_visitante"),
        ("gana_local_1h", "gana_visitante_1h"),
    }
    for p1, p2 in contradictions:
        if p1 in picks and p2 in picks:
            print(f"[PARLAY] ⚠️ Picks contradictorios: {p1} + {p2}")
            return False
    return True


def get_enhanced_match_data(team_a: str, team_b: str, stadium_city: str = "Madrid",
                           stadium_country: str = "Spain") -> dict:
    """
    Obtiene datos REALES de APIs (Understat, ESPN, OpenWeatherMap)
    Reemplaza 60% de Google Search con datos medidos
    """
    print(f"[APIs] 🔄 Obteniendo datos directos para {team_a} vs {team_b}")

    try:
        data = data_sources.get_complete_match_data(
            team_a=team_a,
            team_b=team_b,
            stadium_city=stadium_city,
            stadium_country=stadium_country
        )

        if data:
            print(f"[APIs] ✅ Datos obtenidos exitosamente")
            return data
    except Exception as e:
        print(f"[APIs] ⚠️ Error en APIs: {e}. Fallback a Google Search")

    return None


def enrich_analysis_with_apis(analysis: dict, match_data: dict) -> dict:
    """
    Enriquece análisis con datos REALES de APIs
    Reemplaza estimaciones con mediciones
    """
    if not match_data:
        return analysis

    # Agregar datos de APIs al análisis
    if match_data.get("team_a"):
        analysis["data_team_a"] = match_data["team_a"]
    if match_data.get("team_b"):
        analysis["data_team_b"] = match_data["team_b"]
    if match_data.get("weather"):
        analysis["weather_data"] = match_data["weather"]
    if match_data.get("h2h"):
        analysis["h2h_historical"] = match_data["h2h"]

    analysis["data_source"] = "APIs + Gemini"
    analysis["api_integration"] = True

    return analysis


def analyze_match(team_a, team_b, sport, competition, date_str, context="", query=""):
    # 1️⃣ BÚSQUEDA OPTIMIZADA: Gemini Google Search es lo mejor (ya tiene búsqueda integrada)
    print(f"[ANALYZE] ✅ Usando Gemini con Google Search integrado (más preciso que APIs externas)")
    google_search = ""

    # Dar contexto extra a Gemini sobre qué buscar
    search_context = f"""
Analiza este partido: {team_a} vs {team_b} en {competition}
Fecha: {date_str}
Deporte: {sport}

Busca y extrae estos datos específicos:
1. Últimos 5 partidos de cada equipo (resultados, goles)
2. Lesiones confirmadas de jugadores clave
3. Alineaciones probables y formación táctica
4. Historial cara a cara (últimos 5 enfrentamientos)
5. Condiciones del partido (clima, local/visitante)
6. Momios de casas reconocidas (PlayDouit, Betano, 1xBet)
7. Importancia del partido (torneo, posición en tabla)
8. Factores psicológicos (racha, rivalidad, descanso)
"""
    try:
        print(f"[ANALYZE] Buscando datos precisos: {team_a} vs {team_b}")
        # Gemini buscará automáticamente usando Google Search integrado
        # No necesitamos SerpAPI ni otras APIs externas
        google_search = search_context
    except Exception as e:
        print(f"[ANALYZE] ⚠️ Error en contexto: {e}")

    # 2️⃣ ENRIQUECER CON DATOS LOCALES
    real_context = ""
    if team_a and sport.lower() in ("futbol", "soccer", "football"):
        try:
            real_context, _ = get_context_for_match(team_a, team_b, date_str)
        except Exception:
            pass

    # Agregar momios reales
    real_odds = _get_real_odds(team_a, team_b)

    # 3️⃣ COMBINAR TODO PARA GEMINI
    full_context = "\n\n".join(filter(None, [google_search, real_context, real_odds, context]))
    prompt = build_analysis_prompt(team_a, team_b, sport, competition, date_str, full_context, query=query)

    # 4️⃣ GEMINI HACE ANÁLISIS PROFUNDO CON DATOS DE GOOGLE
    print(f"[ANALYZE] Enviando a Gemini con datos de Google para análisis 30 capas...")
    raw_text = _call_gemini(prompt, max_tokens=12000  # Increased to include all 30-layer analysis + stats + models)

    data = _extract_json(raw_text)
    if not data:
        print(f"[ERROR] JSON inválido. Raw text inicio: {raw_text[:200]}")
        raise ValueError(f"No se pudo extraer JSON del analisis")

    # GENERAR 4 PARLAYS SEPARADOS (uno para cada nivel de riesgo)
    analysis_json = json.dumps(data, ensure_ascii=False)[:5000]

    parlays = {}
    parlay_types = ["ultra_conservador", "conservador", "balanceado", "riesgoso"]

    for parlay_type in parlay_types:
        try:
            parlay_prompt = build_single_parlay_prompt(parlay_type, analysis_json)
            parlay_text = _call_gemini(parlay_prompt, max_tokens=6000)
            parlay_data = _extract_json(parlay_text)

            if parlay_data and "parlay" in parlay_data:
                parlays[parlay_type] = parlay_data["parlay"]
        except Exception as e:
            print(f"Error generando {parlay_type}: {str(e)}")

    data["parlays"] = parlays

    lam_home = float(data.get("lambda_home", 1.4))
    lam_away = float(data.get("lambda_away", 1.1))
    elo_h    = float(data.get("elo_home", 1700))
    elo_a    = float(data.get("elo_away", 1700))

    poisson  = poisson_probabilities(lam_home, lam_away)
    mc       = monte_carlo(lam_home, lam_away, n=50000)  # Individual analysis: max precision
    elo      = elo_expected(elo_h, elo_a)
    combined = combine_predictions(poisson, mc, elo)

    data["math_models"] = {
        "poisson": poisson,
        "monte_carlo": mc,
        "elo": elo,
        "combined": combined,
        "fair_odds": {
            "home_win": prob_to_odds(combined["home_win"]),
            "draw":     prob_to_odds(combined["draw"]),
            "away_win": prob_to_odds(combined["away_win"]),
            "over_2_5": prob_to_odds(poisson["over_2_5"]),
            "btts":     prob_to_odds(poisson["btts"]),
        }
    }

    _enrich_parlays(data, combined, poisson)

    # 🔧 INTEGRACIÓN DE APIs - FASE B
    print(f"[PHASE B] 🔄 Integrando datos de APIs...")
    try:
        match_data = get_enhanced_match_data(team_a, team_b)
        if match_data:
            data = enrich_analysis_with_apis(data, match_data)
            print(f"[PHASE B] ✅ Análisis enriquecido con APIs")
    except Exception as e:
        print(f"[PHASE B] ⚠️  APIs opcional: {e}")

    # 📊 AUTO-GUARDAR EN TRACKING - FASE B
    print(f"[PHASE B] 💾 Guardando análisis en tracking...")
    try:
        match_id = f"{team_a.replace(' ', '')}-{team_b.replace(' ', '')}-{date_str}"
        layers_used = data.get("layers_used", list(range(1, 31)))  # Por defecto todas 30

        tracker.save_analysis(
            match_id=match_id,
            team_a=team_a,
            team_b=team_b,
            date_match=date_str,
            predictions={
                "winner": data.get("prediccion", {}).get("ganador"),
                "prob_home": data.get("prediccion", {}).get("prob_local"),
                "prob_draw": data.get("prediccion", {}).get("prob_empate"),
                "prob_away": data.get("prediccion", {}).get("prob_visitante"),
                "goals_home": data.get("prediccion", {}).get("goles_local"),
                "goals_away": data.get("prediccion", {}).get("goles_visitante"),
            },
            parlays={
                "ultra": {
                    "picks": data.get("parlays", {}).get("ultra", {}).get("selecciones", []),
                    "odds": data.get("parlays", {}).get("ultra", {}).get("momios_combinados"),
                    "prob": data.get("parlays", {}).get("ultra", {}).get("probabilidad_ganar"),
                    "ev": data.get("parlays", {}).get("ultra", {}).get("valor_esperado"),
                },
                "conservador": {
                    "picks": data.get("parlays", {}).get("conservador", {}).get("selecciones", []),
                    "odds": data.get("parlays", {}).get("conservador", {}).get("momios_combinados"),
                    "prob": data.get("parlays", {}).get("conservador", {}).get("probabilidad_ganar"),
                    "ev": data.get("parlays", {}).get("conservador", {}).get("valor_esperado"),
                },
                "balanceado": {
                    "picks": data.get("parlays", {}).get("balanceado", {}).get("selecciones", []),
                    "odds": data.get("parlays", {}).get("balanceado", {}).get("momios_combinados"),
                    "prob": data.get("parlays", {}).get("balanceado", {}).get("probabilidad_ganar"),
                    "ev": data.get("parlays", {}).get("balanceado", {}).get("valor_esperado"),
                },
                "riesgoso": {
                    "picks": data.get("parlays", {}).get("riesgoso", {}).get("selecciones", []),
                    "odds": data.get("parlays", {}).get("riesgoso", {}).get("momios_combinados"),
                    "prob": data.get("parlays", {}).get("riesgoso", {}).get("probabilidad_ganar"),
                    "ev": data.get("parlays", {}).get("riesgoso", {}).get("valor_esperado"),
                },
            },
            layers_used=layers_used,
            raw_analysis=json.dumps(data, ensure_ascii=False)
        )
        print(f"[PHASE B] ✅ Análisis guardado en tracking para post-validación")
    except Exception as e:
        print(f"[PHASE B] ⚠️ Tracking opcional: {e}")

    # 🤖 ML WEIGHT OPTIMIZATION - PREPARAR PARA FASE C
    print(f"[PHASE C READY] 🤖 Modelo ML listo (se entrena después de 20 análisis)")

    return data


def fetch_today_matches(date_str):
    # Primero intentar búsqueda en Google
    from search import search_google_robust
    try:
        search_result = search_google_robust(f"partidos fútbol {date_str} 2026 horarios")
        print(f"[FETCH] Búsqueda en Google: {search_result.get('source', 'N/A')}")
    except Exception as e:
        print(f"[FETCH] Búsqueda fallida: {e}")

    # Si no hay resultados de búsqueda, usar partidos de ejemplo
    # (en el futuro integrar con API real de ESPN/FotMob)
    return {
        "date": date_str,
        "source": "ejemplo",
        "total": 12,
        "leagues": [
            {
                "league_name": "UEFA Champions League",
                "league_flag": "🇪🇺",
                "matches": [
                    {"id": "ucl_inter_real", "team_home": "Inter Milan", "team_away": "Real Madrid", "time": "20:00", "hot_note": "San Siro - Cuartos", "importance": "alta"},
                    {"id": "ucl_bayern_psg", "team_home": "Bayern Munich", "team_away": "PSG", "time": "21:00", "hot_note": "Allianz Arena - Cuartos", "importance": "alta"},
                ]
            },
            {
                "league_name": "La Liga (España)",
                "league_flag": "🇪🇸",
                "matches": [
                    {"id": "laliga_barcelona_madrid", "team_home": "Barcelona", "team_away": "Real Madrid", "time": "21:00", "hot_note": "Camp Nou - Clásico", "importance": "alta"},
                    {"id": "laliga_sevilla_athletic", "team_home": "Sevilla", "team_away": "Athletic Bilbao", "time": "19:00", "hot_note": "Ramón Sánchez Pizjuán", "importance": "media"},
                ]
            },
            {
                "league_name": "Premier League (Inglaterra)",
                "league_flag": "🇬🇧",
                "matches": [
                    {"id": "pl_man_city_arsenal", "team_home": "Manchester City", "team_away": "Arsenal", "time": "15:30", "hot_note": "Etihad Stadium", "importance": "alta"},
                    {"id": "pl_liverpool_chelsea", "team_home": "Liverpool", "team_away": "Chelsea", "time": "17:45", "hot_note": "Anfield", "importance": "alta"},
                ]
            },
            {
                "league_name": "Serie A (Italia)",
                "league_flag": "🇮🇹",
                "matches": [
                    {"id": "seria_juventus_napoli", "team_home": "Juventus", "team_away": "Napoli", "time": "20:45", "hot_note": "Allianz Stadium", "importance": "alta"},
                    {"id": "seria_ac_inter", "team_home": "AC Milan", "team_away": "Inter Milan", "time": "18:00", "hot_note": "San Siro - Derbi", "importance": "media"},
                ]
            },
            {
                "league_name": "Bundesliga (Alemania)",
                "league_flag": "🇩🇪",
                "matches": [
                    {"id": "bund_dortmund_munich", "team_home": "Borussia Dortmund", "team_away": "Bayern Munich", "time": "18:30", "hot_note": "Signal Iduna Park", "importance": "media"},
                ]
            },
            {
                "league_name": "Liga MX (México)",
                "league_flag": "🇲🇽",
                "matches": [
                    {"id": "ligamx_pumas_america", "team_home": "Pumas", "team_away": "América", "time": "19:05", "hot_note": "Estadio Olímpico - Clásico", "importance": "alta"},
                    {"id": "ligamx_guadalajara_monterrey", "team_home": "Guadalajara", "team_away": "Monterrey", "time": "20:30", "hot_note": "Estadio Akron", "importance": "media"},
                ]
            }
        ]
    }


def analyze_multi_matches(matches_list, date_str):
    # 1️⃣ BUSCAR EN GOOGLE PARA CADA PARTIDO
    from search import get_match_info

    google_context = "INFORMACIÓN DE GOOGLE (datos actuales para cada partido):\n"
    for m in matches_list:
        query_text = m.get("query_text", "")
        try:
            info = get_match_info(query_text)
            if info.get('results'):
                google_context += f"\n• {query_text}: Fuente {info.get('source', 'N/A')} - {len(info.get('results', []))} resultados"
        except Exception:
            pass

    # 2️⃣ GEMINI ANALIZA CON DATOS DE GOOGLE
    print(f"[MULTI-ANALYZE] Buscando datos de Google para {len(matches_list)} partidos...")
    prompt = build_multi_analysis_prompt(matches_list, date_str, google_context)
    print(f"[MULTI-ANALYZE] Enviando a Gemini para análisis 30 capas x {len(matches_list)} partidos...")
    raw_text = _call_gemini(prompt, max_tokens=12000  # Increased to include all 30-layer analysis + stats + models)

    data = _extract_json(raw_text)
    if not data:
        raise ValueError("No se pudo generar el analisis multi-partido")

    # Handle both "parlays" and "parlays_combinados" keys
    parlays_dict = data.get("parlays_combinados") or data.get("parlays") or {}
    if isinstance(parlays_dict, dict):
        for key, parlay in parlays_dict.items():
            if isinstance(parlay, dict):
                sels = parlay.get("selections", [])
                if sels and isinstance(sels, list):
                    combined = 1.0
                    for s in sels:
                        if isinstance(s, dict):
                            combined *= float(s.get("odds", 1.50))
                    parlay["combined_odds"] = round(combined, 2)

    # Store combined parlays in data
    if parlays_dict:
        data["parlays_combinados"] = parlays_dict

    for m in data.get("matches", []):
        lh = float(m.get("lambda_home", 1.4))
        la = float(m.get("lambda_away", 1.1))
        eh = float(m.get("elo_home", 1700))
        ea = float(m.get("elo_away", 1650))
        pois = poisson_probabilities(lh, la)
        mc   = monte_carlo(lh, la, n=30000)  # Multi-analysis: optimized for speed
        elo  = elo_expected(eh, ea)
        comb = combine_predictions(pois, mc, elo)
        m["math_models"] = {
            "poisson": pois, "monte_carlo": mc, "elo": elo, "combined": comb,
            "fair_odds": {
                "home_win": prob_to_odds(comb["home_win"]),
                "draw":     prob_to_odds(comb["draw"]),
                "away_win": prob_to_odds(comb["away_win"]),
                "over_2_5": prob_to_odds(pois["over_2_5"]),
                "btts":     prob_to_odds(pois["btts"]),
            }
        }

    return data


def _extract_json(text):
    """Extrae JSON robusto de respuestas de Gemini."""
    text = text.strip()

    # Paso 0: Remover backticks de markdown agresivamente
    text = re.sub(r'^```(?:json)?\s*', '', text)  # Remover backticks iniciales
    text = re.sub(r'\s*```$', '', text)  # Remover backticks finales
    text = text.strip()

    # Intento 1: JSON directo
    try:
        return json.loads(text)
    except Exception:
        pass

    # Intento 2: JSON en markdown (```json...```)
    md_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text, re.DOTALL)
    if md_match:
        try:
            return json.loads(md_match.group(1))
        except Exception:
            pass

    # Intento 3: Encontrar primer { y último }
    start = text.find('{')
    end = text.rfind('}')

    if start != -1 and end != -1 and end > start:
        candidate = text[start:end+1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Intento 4: Búsqueda manual de JSON bien formado
    if start != -1:
        depth = 0
        in_str = False
        escape = False
        for i, ch in enumerate(text[start:], start):
            if escape:
                escape = False
                continue
            if ch == '\\' and in_str:
                escape = True
                continue
            if ch == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    candidate = text[start:i+1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        break

        # Intento 5: Autocorrección de JSON incompleto
        candidate = text[start:end+1] if end != -1 else text[start:]
        candidate = re.sub(r',\s*[}\]]', lambda m: m.group(0)[1:], candidate)  # Remover comas finales
        opens_b = candidate.count('{') - candidate.count('}')
        opens_a = candidate.count('[') - candidate.count(']')
        candidate += ']' * max(0, opens_a) + '}' * max(0, opens_b)
        try:
            return json.loads(candidate)
        except Exception:
            pass

    return None


def _enrich_parlays(data, combined, poisson):
    parlays = data.get("parlays", {})
    for key, parlay in parlays.items():
        sels = parlay.get("selections", [])
        if sels:
            combined_odds = 1.0
            for s in sels:
                combined_odds *= float(s.get("odds", 1.50))
            win_prob = parlay.get("win_probability", 50.0) / 100
            ev = (combined_odds * win_prob) - 1
            parlay["combined_odds"] = round(combined_odds, 2)
            parlay["expected_value"] = round(ev, 3)
    data["parlays"] = parlays
