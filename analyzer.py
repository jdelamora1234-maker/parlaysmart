import os, json, re
import anthropic
from models import poisson_probabilities, monte_carlo, combine_predictions, elo_expected, prob_to_odds
from prompts import SYSTEM_PROMPT, build_analysis_prompt

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def analyze_match(team_a, team_b, sport, competition, date_str, context="", query=""):
    prompt = build_analysis_prompt(team_a, team_b, sport, competition, date_str, context, query=query)

    tools = [{
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 15,
    }]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        tools=tools,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            raw_text += block.text

    data = _extract_json(raw_text)
    if not data:
        raise ValueError(f"No se pudo extraer JSON del análisis. Respuesta: {raw_text[:500]}")

    lam_home = float(data.get("lambda_home", 1.4))
    lam_away = float(data.get("lambda_away", 1.1))
    elo_h    = float(data.get("elo_home", 1700))
    elo_a    = float(data.get("elo_away", 1700))

    poisson = poisson_probabilities(lam_home, lam_away)
    mc      = monte_carlo(lam_home, lam_away, n=50000)
    elo     = elo_expected(elo_h, elo_a)
    combined = combine_predictions(poisson, mc, elo)

    data["math_models"] = {
        "poisson": poisson,
        "monte_carlo": mc,
        "elo": elo,
        "combined": combined,
        "fair_odds": {
            "home_win":  prob_to_odds(combined["home_win"]),
            "draw":      prob_to_odds(combined["draw"]),
            "away_win":  prob_to_odds(combined["away_win"]),
            "over_2_5":  prob_to_odds(poisson["over_2_5"]),
            "btts":      prob_to_odds(poisson["btts"]),
        }
    }

    _enrich_parlays(data, combined, poisson)
    return data

def _extract_json(text):
    text = text.strip()
    # Intentar parsear directo
    try:
        return json.loads(text)
    except Exception:
        pass
    # Extraer de bloque markdown ```json ... ```
    md_match = re.search(r'```(?:json)?\s*(\{[\s\S]+?\})\s*```', text)
    if md_match:
        try:
            return json.loads(md_match.group(1))
        except Exception:
            pass
    # Buscar el JSON más grande (desde primer { hasta último })
    start = text.find('{')
    end   = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
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
