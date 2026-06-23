import os, json, re, hashlib, requests
from datetime import date as dt_date
import google.generativeai as genai
from models import poisson_probabilities, monte_carlo, combine_predictions, elo_expected, prob_to_odds
from prompts import SYSTEM_PROMPT, build_analysis_prompt, build_today_matches_prompt, build_multi_analysis_prompt
from football_api import get_context_for_match, get_fixtures_for_mx_date, fixtures_to_matches

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
ODDS_API_KEY = os.environ.get("ODDS_API_KEY")

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_key(*parts):
    raw = "|".join(str(p).lower().strip() for p in parts)
    return hashlib.md5(raw.encode()).hexdigest()

def _cache_get(key):
    path = os.path.join(CACHE_DIR, key + ".json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        entry = json.load(f)
    if entry.get("date") != str(dt_date.today()):
        return None
    return entry.get("data")

def _cache_set(key, data):
    path = os.path.join(CACHE_DIR, key + ".json")
    with open(path, "w") as f:
        json.dump({"date": str(dt_date.today()), "data": data}, f)

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

def _call_gemini(prompt, max_tokens=12000):
    full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    response = model.generate_content(full_prompt, generation_config=genai.types.GenerationConfig(max_output_tokens=max_tokens))
    return response.text

def analyze_match(team_a, team_b, sport, competition, date_str, context="", query=""):
    ck = _cache_key(query or f"{team_a}_{team_b}", date_str)
    cached = _cache_get(ck)
    if cached:
        cached["_cached"] = True
        return cached

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
    raw_text = _call_gemini(prompt, max_tokens=6000)

    data = _extract_json(raw_text)
    if not data:
        raise ValueError(f"No se pudo extraer JSON del analisis. Respuesta: {raw_text[:500]}")

    lam_home = float(data.get("lambda_home", 1.4))
    lam_away = float(data.get("lambda_away", 1.1))
    elo_h    = float(data.get("elo_home", 1700))
    elo_a    = float(data.get("elo_away", 1700))

    poisson  = poisson_probabilities(lam_home, lam_away)
    mc       = monte_carlo(lam_home, lam_away, n=50000)
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
    _cache_set(ck, data)
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
    ids = "_".join(sorted(m.get("query_text") or m.get("id","") for m in matches_list))
    ck = _cache_key("multi", ids, date_str)
    cached = _cache_get(ck)
    if cached:
        cached["_cached"] = True
        return cached

    prompt = build_multi_analysis_prompt(matches_list, date_str)
    raw_text = _call_gemini(prompt, max_tokens=10000)

    data = _extract_json(raw_text)
    if not data:
        raise ValueError("No se pudo generar el analisis multi-partido")

    for parlay in data.get("parlays", []):
        sels = parlay.get("selections", [])
        if sels:
            combined = 1.0
            for s in sels:
                combined *= float(s.get("odds", 1.50))
            parlay["combined_odds"] = round(combined, 2)

    for m in data.get("matches", []):
        lh = float(m.get("lambda_home", 1.4))
        la = float(m.get("lambda_away", 1.1))
        eh = float(m.get("elo_home", 1700))
        ea = float(m.get("elo_away", 1650))
        pois = poisson_probabilities(lh, la)
        mc   = monte_carlo(lh, la, n=20000)
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


def predict_tournament(tournament):
    ck = _cache_key("tournament", tournament)
    cached = _cache_get(ck)
    if cached:
        return cached

    prompt = f"""Eres un experto en analisis deportivo. Analiza y predice el torneo: "{tournament}"

Usa Google Search para obtener informacion actualizada: equipos participantes, forma reciente, lesionados clave, momios actuales de las casas de apuestas.

Responde UNICAMENTE con JSON valido con esta estructura:
{{
  "tournament_name": "nombre completo del torneo",
  "current_stage": "fase actual o proxima fase",
  "predicted_winner": "equipo o seleccion ganadora",
  "winner_probability": "XX%",
  "winner_reason": "explicacion breve en 1-2 oraciones de por que ganara",
  "top_contenders": [
    {{"team": "nombre", "probability": "XX%", "reason": "fortaleza principal"}},
    {{"team": "nombre", "probability": "XX%", "reason": "fortaleza principal"}},
    {{"team": "nombre", "probability": "XX%", "reason": "fortaleza principal"}},
    {{"team": "nombre", "probability": "XX%", "reason": "fortaleza principal"}},
    {{"team": "nombre", "probability": "XX%", "reason": "fortaleza principal"}}
  ],
  "group_predictions": [
    {{
      "group": "A",
      "teams": [
        {{"team": "nombre", "points": 9}},
        {{"team": "nombre", "points": 6}},
        {{"team": "nombre", "points": 3}},
        {{"team": "nombre", "points": 0}}
      ]
    }}
  ],
  "bracket": [
    {{
      "round": "Cuartos de Final",
      "matches": [
        {{"team_a": "nombre", "team_b": "nombre", "predicted_winner": "nombre", "predicted_score": "2-1"}}
      ]
    }}
  ],
  "analysis": "Parrafo con el analisis general del torneo, favoritos, sorpresas posibles y factores clave"
}}

Si es un torneo de grupos incluye group_predictions con TODOS los grupos.
Si ya esta en fase eliminatoria incluye bracket con las rondas restantes.
Si es una liga regular, omite bracket y group_predictions y enfoca en top_contenders."""

    raw = _call_gemini(prompt, max_tokens=8000)
    data = _extract_json(raw)
    if not data:
        raise ValueError("No se pudo generar la prediccion del torneo")
    _cache_set(ck, data)
    return data


def _extract_json(text):
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    md_match = re.search(r'```(?:json)?\s*(\{[\s\S]+\})\s*```', text)
    if md_match:
        try:
            return json.loads(md_match.group(1))
        except Exception:
            pass
    start = text.find('{')
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
        candidate = text[start:]
        candidate = re.sub(r',\s*$', '', candidate)
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
