SYSTEM_PROMPT = """Eres experto en análisis de fútbol. Devuelve SOLO JSON válido (sin markdown, sin explicaciones).
Analiza: estadísticas, tácticas, lesiones, forma reciente, momios, value bets.
Responde ÚNICAMENTE con JSON válido sin marcas de código."""


def build_single_parlay_prompt(parlay_type, match_analysis_json):
    """Genera UN SOLO parlay específico basándose en el análisis previo."""
    descriptions = {
        "ultra_conservador": "1 pick ultra-seguro, probabilidad ~75%, momios ~1.65, EV+ confirmado",
        "conservador": "2 picks de alta probabilidad, probabilidad ~55%, momios combinados ~3.0, ambos EV+",
        "balanceado": "3 picks con valor explorado, probabilidad ~38%, momios combinados ~6.0, todos EV+",
        "riesgoso": "4 picks de alto valor, probabilidad ~18%, momios combinados ~16.5, máxima ganancia potencial"
    }

    desc = descriptions.get(parlay_type, "")
    return f"""Basándote EXACTAMENTE en este análisis: {match_analysis_json}

Genera SOLO el parlay "{parlay_type}" ({desc}) en JSON válido:

{{
  "parlay": {{
    "type": "{parlay_type}",
    "selections": [
      {{"market": "nombre mercado", "pick": "descripcion", "odds": 1.70, "reason": "razon con datos"}}
    ],
    "combined_odds": 1.70,
    "win_probability": 75,
    "expected_value": 0.12,
    "strategy": "descripcion estrategia",
    "stake_suggestion": "porcentaje del presupuesto"
  }}
}}"""

def build_parlays_prompt(match_analysis_json):
    """Genera SOLO los 4 parlays basándose en el análisis previo."""
    return f"""Basándote en este análisis: {match_analysis_json}

Genera SOLO los 4 parlays (ultra_conservador, conservador, balanceado, riesgoso) en este JSON (SIN nada más):

{{
  "parlays": {{
    "ultra_conservador": {{
      "name": "Ultra Conservador",
      "risk_level": 1,
      "risk_color": "green",
      "selections": [
        {{"market": "nombre mercado", "pick": "descripcion", "odds": 1.65, "reason": "justificacion"}}
      ],
      "combined_odds": 1.65,
      "win_probability": 75,
      "expected_value": 0.12,
      "strategy": "1 pick ultra-seguro",
      "stake_suggestion": "30-40% de presupuesto"
    }},
    "conservador": {{
      "name": "Conservador",
      "risk_level": 3,
      "risk_color": "blue",
      "selections": [
        {{"market": "mercado 1", "pick": "pick 1", "odds": 1.70, "reason": "razon"}},
        {{"market": "mercado 2", "pick": "pick 2", "odds": 1.80, "reason": "razon"}}
      ],
      "combined_odds": 3.06,
      "win_probability": 55,
      "expected_value": 0.18,
      "strategy": "2 picks de alta probabilidad",
      "stake_suggestion": "20-25% de presupuesto"
    }},
    "balanceado": {{
      "name": "Balanceado",
      "risk_level": 5,
      "risk_color": "gold",
      "selections": [
        {{"market": "m1", "pick": "p1", "odds": 1.80, "reason": "r1"}},
        {{"market": "m2", "pick": "p2", "odds": 1.90, "reason": "r2"}},
        {{"market": "m3", "pick": "p3", "odds": 1.75, "reason": "r3"}}
      ],
      "combined_odds": 5.99,
      "win_probability": 38,
      "expected_value": 0.22,
      "strategy": "3 picks con valor",
      "stake_suggestion": "15% de presupuesto"
    }},
    "riesgoso": {{
      "name": "Riesgoso",
      "risk_level": 8,
      "risk_color": "red",
      "selections": [
        {{"market": "m1", "pick": "p1", "odds": 2.20, "reason": "r1"}},
        {{"market": "m2", "pick": "p2", "odds": 2.50, "reason": "r2"}},
        {{"market": "m3", "pick": "p3", "odds": 3.00, "reason": "r3"}}
      ],
      "combined_odds": 16.5,
      "win_probability": 18,
      "expected_value": 0.35,
      "strategy": "picks de alto valor",
      "stake_suggestion": "5-10% de presupuesto"
    }}
  }}
}}"""

def build_analysis_prompt(team_a, team_b, sport, competition, date_str, context="", query=""):
    return f"""{team_a} vs {team_b}. {competition}.
{context}

JSON con 4 parlays + estadísticas:
{{
  "winner": "team_a/draw/team_b",
  "confidence": 8,
  "team_a_stats": {{"goals_avg": 1.5, "possession": 55, "xg": 1.8, "key_players": "nombres"}},
  "team_b_stats": {{"goals_avg": 1.2, "possession": 45, "xg": 1.3, "key_players": "nombres"}},
  "parlays": {{
    "ultra_conservador": {{"picks": 1, "odds": 1.75, "prob": 75, "reason": "máxima seguridad"}},
    "conservador": {{"picks": 2, "odds": 3.5, "prob": 55, "reason": "riesgo bajo"}},
    "balanceado": {{"picks": 3, "odds": 6.3, "prob": 40, "reason": "equilibrio"}},
    "riesgoso": {{"picks": 4, "odds": 20.0, "prob": 18, "reason": "máximo valor"}}
  }},
  "lambda_home": 1.4,
  "lambda_away": 1.1,
  "elo_home": 1700,
  "elo_away": 1650
}}"""


def build_today_matches_prompt(date_str):
    return f"""Partidos de fútbol para {date_str}. Incluye: Mundial, Copa América, Champions, La Liga, Premier, Liga MX, etc.

Devuelve SOLO JSON (sin markdown):

{{
  "date": "{date_str}",
  "leagues": [
    {{
      "league_name": "World Cup",
      "league_flag": "",
      "matches": [
        {{
          "id": "string_unico_sin_espacios",
          "team_home": "Nombre equipo local",
          "team_away": "Nombre equipo visitante",
          "time": "11:00",
          "hot_note": "Grupo A - AT&T Stadium Dallas" ,
          "importance": "alta"
        }}
      ]
    }}
  ]
}}"""


def build_multi_analysis_prompt(matches_list, date_str, raw_queries=None):
    n = len(matches_list)
    match_lines = []
    for i, m in enumerate(matches_list, 1):
        qt = m.get("query_text") or f"{m.get('team_home','')} vs {m.get('team_away','')}"
        league = m.get("league_name", "")
        time_mx = m.get("time_mx", "")
        match_lines.append(f"  Partido {i}: {qt}" + (f" | {league}" if league else "") + (f" | {time_mx}" if time_mx else ""))
    matches_text = "\n".join(match_lines)

    return f"""Analiza en profundidad los siguientes {n} partidos del {date_str} aplicando el protocolo de 30 capas para cada uno:

{matches_text}

BUSQUEDA OBLIGATORIA POR PARTIDO:
- Estadisticas avanzadas: xG, xGA, PPDA (FBref, Sofascore, Understat)
- Lesiones y suspensiones confirmadas
- PRIORIDAD: Momios actuales de PlayDouit (playdoit.mx) para TODOS los mercados
- Caliente, 1xBet como referencia comparativa
- Forma reciente, head to head, contexto de importancia
- Perfil del arbitro designado
- Condiciones meteorologicas y estado del estadio
- Noticias ultimas 48h, estado del vestuario

CAPAS OBLIGATORIAS A EVALUAR:
- Capa 5 (Psicologia): multiplicador de motivacion, factor revancha, resiliencia emocional
- Capa 9 (Fatiga): horas de descanso, congestion de calendario, jet lag
- Capa 15 (Mercado): dropping odds en PlayDouit, sesgo de aficionado
- Capa 17 (Modelos): Poisson, Elo, Monte Carlo mental para True Odds
- Capa 25 (Ineficiencias PlayDouit): prop bets mal calculadas, latencia de cuotas
- Capa 26 (Value bets): correlacion cruzada inversa, sesgo del aficionado en equipos populares
- Capa 30 (VAR): si hay historial de partidos con revisiones largas, incluir trigger live

Genera parlays combinando los mejores picks de TODOS los partidos con momios de PlayDouit.

Devuelve SOLO este JSON (sin texto ni markdown antes o despues):

{{
  "analysis_date": "{date_str}",
  "total_matches": {n},
  "ego_summary": "Resumen de factores psicologicos y de mercado mas relevantes del dia",
  "matches": [
    {{
      "id": "string",
      "team_home": "...",
      "team_away": "...",
      "league": "...",
      "time_mx": "...",
      "confidence": 8,
      "recommended_pick": "H",
      "pick_label": "Local gana",
      "main_market": "1X2",
      "recommended_odds": 1.85,
      "alt_market": "Over 2.5 goles",
      "alt_odds": 1.75,
      "key_stat": "razon principal en 1 linea con datos cuantitativos",
      "form_home": ["W","W","D","L","W"],
      "form_away": ["L","W","W","D","L"],
      "injury_alert": "descripcion o null",
      "lambda_home": 1.4,
      "lambda_away": 1.1,
      "elo_home": 1700,
      "elo_away": 1650,
      "stats_home": {{
        "goals_scored_avg": 0.0, "goals_conceded_avg": 0.0, "xg_avg": 0.0,
        "xga_avg": 0.0, "ppda": 0.0, "possession_avg": 0.0,
        "shots_per_game": 0.0, "clean_sheets": 0, "clean_sheets_pct": 0.0,
        "btts_rate": 0.0, "over_2_5_rate": 0.0, "home_record": "W-D-L",
        "avg_goals_first_half": 0.0, "avg_goals_second_half": 0.0,
        "fatigue_index": 0, "motivation_multiplier": 1.0
      }},
      "stats_away": {{
        "goals_scored_avg": 0.0, "goals_conceded_avg": 0.0, "xg_avg": 0.0,
        "xga_avg": 0.0, "ppda": 0.0, "possession_avg": 0.0,
        "shots_per_game": 0.0, "clean_sheets": 0, "clean_sheets_pct": 0.0,
        "btts_rate": 0.0, "over_2_5_rate": 0.0, "away_record": "W-D-L",
        "avg_goals_first_half": 0.0, "avg_goals_second_half": 0.0,
        "fatigue_index": 0, "motivation_multiplier": 1.0
      }},
      "head_to_head": {{
        "total_meetings": 0, "home_wins": 0, "draws": 0, "away_wins": 0,
        "avg_goals": 0.0, "btts_rate": 0.0, "over_2_5_rate": 0.0,
        "last_3": ["resultado 1", "resultado 2", "resultado 3"],
        "tactical_tendency": "tiende a cerrado/abierto"
      }},
      "markets": {{
        "btts": {{"prob": 0.0, "odds": 0.0, "rec": "si/no"}},
        "over_2_5": {{"prob": 0.0, "odds": 0.0, "rec": "si/no"}},
        "over_1_5": {{"prob": 0.0, "odds": 0.0, "rec": "si/no"}},
        "home_win": {{"prob": 0.0, "odds": 0.0, "rec": "si/no"}},
        "draw": {{"prob": 0.0, "odds": 0.0, "rec": "si/no"}},
        "away_win": {{"prob": 0.0, "odds": 0.0, "rec": "si/no"}},
        "double_chance_1x": {{"prob": 0.0, "odds": 0.0, "rec": "si/no"}}
      }},
      "diagnostic_table": {{
        "prob_home_true": 0.0,
        "prob_draw_true": 0.0,
        "prob_away_true": 0.0,
        "true_xg_total": 0.0,
        "fatigue_delta": 0,
        "chaos_index": 5,
        "playdoit_inefficiency": "mercado / cuota",
        "value_edge": "mercado / cuota minima"
      }},
      "playdoit_inefficiency": {{
        "detected": false,
        "market": "mercado mal calculado o ninguno",
        "playdoit_odds": 0.0,
        "true_odds": 0.0,
        "ev_pct": 0.0,
        "reason": "explicacion o ninguna"
      }},
      "live_triggers": [
        {{"trigger": "evento", "action": "accion", "market": "mercado", "reasoning": "razon"}}
      ],
      "final_prediction": {{
        "winner": "team_home/draw/team_away",
        "confidence": 8,
        "score": "2-1",
        "reasoning": "razonamiento de 3-4 oraciones con datos de las 30 capas",
        "key_factors": ["factor 1 con datos", "factor 2 con datos"],
        "risks": ["riesgo 1 cuantificado"],
        "best_bet": "mercado especifico con mayor EV+ en PlayDouit"
      }},
      "mexican_odds": {{
        "playdouit_home": 0.0, "playdouit_draw": 0.0, "playdouit_away": 0.0,
        "playdouit_over_2_5": 0.0, "playdouit_btts_yes": 0.0,
        "caliente_home": 0.0, "caliente_draw": 0.0, "caliente_away": 0.0,
        "1xbet_home": 0.0, "best_value": "mejor valor en PlayDouit"
      }},
      "ego_analysis": {{
        "risk_level": "bajo/medio/alto",
        "star_player_home": "nombre o null",
        "star_ego_note": "estado mental y motivacion del astro",
        "psychological_edge": "home/away/neutral",
        "locker_room_issues": "descripcion o ninguno",
        "revenge_factor": "descripcion o ninguno",
        "pressure_players": ["jugador - tipo de presion"],
        "ego_impact_on_bet": "como afecta el ego a esta apuesta"
      }},
      "individual_parlays": [
        {{
          "name": "Ultra Conservador",
          "risk_level": 1,
          "risk_color": "green",
          "selections": [
            {{"pick": "pick con datos", "market": "1X2", "odds": 1.75, "reason": "razon cuantitativa"}}
          ],
          "combined_odds": 1.75,
          "win_probability": 72,
          "strategy": "1 pick de maxima seguridad con EV+ confirmado en PlayDouit"
        }},
        {{
          "name": "Conservador",
          "risk_level": 3,
          "risk_color": "blue",
          "selections": [
            {{"pick": "pick 1", "market": "1X2", "odds": 1.75, "reason": ""}},
            {{"pick": "pick 2", "market": "Over/Under", "odds": 1.80, "reason": ""}}
          ],
          "combined_odds": 3.15,
          "win_probability": 55,
          "strategy": "2 picks solidos del mismo partido con momios de PlayDouit"
        }},
        {{
          "name": "Balanceado",
          "risk_level": 5,
          "risk_color": "gold",
          "selections": [
            {{"pick": "pick 1", "market": "1X2", "odds": 1.85, "reason": ""}},
            {{"pick": "pick 2", "market": "BTTS", "odds": 1.90, "reason": ""}},
            {{"pick": "pick 3", "market": "Over/Under", "odds": 1.80, "reason": ""}}
          ],
          "combined_odds": 6.32,
          "win_probability": 38,
          "strategy": "3 picks explotando ineficiencias de PlayDouit"
        }},
        {{
          "name": "Riesgoso",
          "risk_level": 8,
          "risk_color": "red",
          "selections": [
            {{"pick": "pick 1", "market": "Marcador exacto", "odds": 5.50, "reason": ""}},
            {{"pick": "pick 2", "market": "1X2", "odds": 2.20, "reason": ""}}
          ],
          "combined_odds": 12.10,
          "win_probability": 18,
          "strategy": "picks donde PlayDouit tiene sesgo explotable de aficionado"
        }}
      ],
      "skip": false,
      "skip_reason": null
    }}
  ],
  "parlays": [
    {{
      "name": "Ultra Conservador",
      "risk_level": 1,
      "risk_color": "green",
      "description": "Solo picks con 70%+ probabilidad real (Monte Carlo), sin factores de ego o fatigue elevados",
      "selections": [
        {{
          "match": "Local vs Visitante",
          "pick": "Local gana",
          "market": "1X2",
          "odds": 1.85,
          "confidence": 8,
          "ego_note": "Sin factores de ego relevantes",
          "playdoit_edge": "cuota implicita vs probabilidad real"
        }}
      ],
      "combined_odds": 3.42,
      "win_probability": 29,
      "expected_value": 0.15,
      "strategy": "Picks donde PlayDouit tiene el overround mas bajo y el EV+ es positivo confirmado",
      "stake_suggestion": "20-30% de tu presupuesto del dia"
    }},
    {{
      "name": "Conservador",
      "risk_level": 3,
      "risk_color": "blue",
      "description": "2-3 picks solidos explotando sesgo de aficionado en PlayDouit",
      "selections": [],
      "combined_odds": 0.0,
      "win_probability": 0,
      "expected_value": 0.0,
      "strategy": "",
      "stake_suggestion": ""
    }},
    {{
      "name": "Balanceado",
      "risk_level": 5,
      "risk_color": "gold",
      "description": "Mix de picks seguros y de valor con ineficiencias de PlayDouit detectadas",
      "selections": [],
      "combined_odds": 0.0,
      "win_probability": 0,
      "expected_value": 0.0,
      "strategy": "",
      "stake_suggestion": ""
    }},
    {{
      "name": "Riesgoso / Bomba",
      "risk_level": 8,
      "risk_color": "red",
      "description": "Picks de alto valor donde el sesgo del aficionado en PlayDouit crea momios inflados",
      "selections": [],
      "combined_odds": 0.0,
      "win_probability": 0,
      "expected_value": 0.0,
      "strategy": "",
      "stake_suggestion": ""
    }}
  ],
  "best_single_pick": {{
    "match": "Local vs Visitante",
    "pick": "...",
    "market": "...",
    "odds": 0.0,
    "confidence": 9,
    "reason": "razon detallada con datos cuantitativos de las 30 capas"
  }},
  "matches_to_avoid": [
    {{ "match": "...", "reason": "chaos_index alto o sin value en PlayDouit" }}
  ]
}}"""
