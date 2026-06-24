import os, json, re, hashlib, requests
from datetime import date as dt_date
from models import poisson_probabilities, monte_carlo, combine_predictions, elo_expected, prob_to_odds
from prompts import SYSTEM_PROMPT, build_analysis_prompt, build_today_matches_prompt, build_multi_analysis_prompt, build_single_parlay_prompt
from football_api import get_context_for_match, get_fixtures_for_mx_date, fixtures_to_matches

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "").strip()

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
    """Llamada a Gemini API usando Google Cloud REST API."""
    import time

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY no está configurada")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"

    for attempt in range(retry):
        try:
            payload = {
                "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}]}],
                "generationConfig": {
                    "maxOutputTokens": min(max_tokens, 8000),
                    "temperature": 0.3,
                }
            }

            resp = requests.post(url, json=payload, timeout=45)

            if resp.status_code != 200:
                error_body = resp.text[:500]
                print(f"[Gemini] HTTP {resp.status_code}: {error_body}")
                raise ValueError(f"HTTP {resp.status_code}: {error_body}")

            try:
                data = resp.json()
            except Exception as json_err:
                print(f"[Gemini] JSON parse error: {resp.text[:300]}")
                raise ValueError(f"JSON parse error: {resp.text[:300]}")

            # Validar estructura de respuesta Gemini
            candidates = data.get("candidates", [])
            if not candidates or len(candidates) == 0:
                print(f"[Gemini] No candidates. Full response: {data}")
                raise ValueError("No candidates en respuesta Gemini")

            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])

            if not parts or len(parts) == 0:
                print(f"[Gemini] No parts. Candidate: {candidate}")
                raise ValueError("No parts en respuesta Gemini")

            text = parts[0].get("text", "").strip()

            if not text:
                print(f"[Gemini] Empty text. Parts: {parts}")
                raise ValueError("Texto vacío en respuesta Gemini")

            return text

        except Exception as e:
            error_msg = str(e)[:200]
            print(f"[Gemini attempt {attempt+1}/{retry}] ERROR: {error_msg}")
            if attempt == retry - 1:
                raise ValueError(f"Gemini error: {error_msg}")
            time.sleep(2)

    raise ValueError("Gemini falló después de reintentos")

def analyze_match(team_a, team_b, sport, competition, date_str, context="", query=""):
    # Enriquecer con datos reales de API-Football
    real_context = ""
    if team_a and sport.lower() in ("futbol", "soccer", "football"):
        try:
            real_context, _ = get_context_for_match(team_a, team_b, date_str)
        except Exception:
            pass

    # Agregar momios reales de The Odds API
    real_odds = _get_real_odds(team_a, team_b)
    full_context = "\n\n".join(filter(None, [real_context, real_odds, context]))
    prompt = build_analysis_prompt(team_a, team_b, sport, competition, date_str, full_context, query=query)
    raw_text = _call_gemini(prompt, max_tokens=12000)

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
    return data


def fetch_today_matches(date_str):
    ck = _cache_key("today_matches", date_str)
    cached = _cache_get(ck)
    if cached:
        return cached

    # 1. Gemini primero (datos actuales: Mundial 2026, temporada en curso)
    try:
        prompt = build_today_matches_prompt(date_str)
        raw_text = _call_gemini(prompt, max_tokens=4000)
        data = _extract_json(raw_text)
        if data:
            total = 0
            for league in data.get("leagues", []):
                for m in league.get("matches", []):
                    if not m.get("id"):
                        m["id"] = (league.get("league_name","") + "_" + m.get("team_home","") + "_" + m.get("team_away","")).lower().replace(" ","_")
                    m["league_name"] = league.get("league_name","")
                    m["league_flag"] = league.get("league_flag","")
                    if not m.get("time") and m.get("time_mx"):
                        m["time"] = m["time_mx"]
                    total += 1
            data["total"] = total
            data["source"] = "gemini"
            _cache_set(ck, data)
            return data
    except Exception as e:
        raise ValueError(f"No se pudieron obtener los partidos: {str(e)}")


def analyze_multi_matches(matches_list, date_str):
    prompt = build_multi_analysis_prompt(matches_list, date_str)
    raw_text = _call_gemini(prompt, max_tokens=12000)

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

    _cache_set(ck, data)
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
