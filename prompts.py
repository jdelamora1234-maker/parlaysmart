SYSTEM_PROMPT = """Eres un analista experto en apuestas deportivas con 15 años de experiencia.
Analizas partidos con rigor estadístico, contexto táctico y conocimiento del mercado de apuestas.
Siempre respondes en español. Eres directo, preciso y objetivo.
Cuando no encuentras datos específicos, lo indicas claramente y usas estimaciones conservadoras.
Tus análisis están basados en evidencia, no en intuición."""

def build_analysis_prompt(team_a, team_b, sport, competition, date_str, context="", query=""):
    if query:
        header = f"""El usuario quiere analizar el siguiente partido (texto libre): "{query}"

Identifica automáticamente: equipo local, equipo visitante, deporte, competición y fecha a partir del texto.
Usa esos datos en el campo "match_info" del JSON de respuesta.
Luego realiza el análisis completo buscando en la web."""
    else:
        header = f"""Analiza el siguiente evento deportivo de forma exhaustiva para apuestas:

**PARTIDO:** {team_a} vs {team_b}
**DEPORTE:** {sport}
**COMPETICIÓN:** {competition}
**FECHA:** {date_str}
{f'**CONTEXTO ADICIONAL:** {context}' if context else ''}"""

    return f"""{header}

Realiza una investigación web completa y proporciona el siguiente análisis en formato JSON estructurado.

Busca información actualizada en: FBref, Sofascore, Understat, FotMob, Flashscore, ESPN, BBC Sport, Transfermarkt y redes sociales oficiales de los equipos.
ADEMÁS busca los momios actuales en casas mexicanas: PlayDouit (playdoit.mx), Caliente (caliente.mx), Codere México, 1xBet México, Bet365 México. Reporta los momios exactos que encuentres en el campo "mexican_odds".

Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta (sin markdown, sin texto extra):

{{
  "match_info": {{
    "team_a": "{team_a}",
    "team_b": "{team_b}",
    "sport": "{sport}",
    "competition": "{competition}",
    "date": "{date_str}"
  }},
  "stats_team_a": {{
    "goals_scored_avg": 0.0,
    "goals_conceded_avg": 0.0,
    "xg_avg": 0.0,
    "xga_avg": 0.0,
    "shots_per_game": 0.0,
    "shots_on_target_per_game": 0.0,
    "possession_avg": 0.0,
    "home_record": "W-D-L",
    "away_record": "W-D-L",
    "last_5": ["W","W","D","L","W"],
    "last_10_wins": 0,
    "current_streak": "descripción",
    "form_rating": 7.0,
    "source_notes": "fuentes consultadas"
  }},
  "stats_team_b": {{
    "goals_scored_avg": 0.0,
    "goals_conceded_avg": 0.0,
    "xg_avg": 0.0,
    "xga_avg": 0.0,
    "shots_per_game": 0.0,
    "shots_on_target_per_game": 0.0,
    "possession_avg": 0.0,
    "home_record": "W-D-L",
    "away_record": "W-D-L",
    "last_5": ["W","L","W","W","D"],
    "last_10_wins": 0,
    "current_streak": "descripción",
    "form_rating": 6.5,
    "source_notes": "fuentes consultadas"
  }},
  "head_to_head": {{
    "last_meetings": 5,
    "team_a_wins": 0,
    "draws": 0,
    "team_b_wins": 0,
    "avg_goals_per_game": 0.0,
    "btts_rate": 0.0,
    "last_results": ["descripción de últimos encuentros"],
    "trend": "descripción de tendencia"
  }},
  "players": {{
    "team_a_key_absences": ["jugador - razón"],
    "team_b_key_absences": ["jugador - razón"],
    "team_a_in_form": ["jugador - stats recientes"],
    "team_b_in_form": ["jugador - stats recientes"],
    "fatigue_risk_a": "bajo/medio/alto",
    "fatigue_risk_b": "bajo/medio/alto",
    "notes": "notas sobre jugadores importantes"
  }},
  "context": {{
    "match_importance": "descripción",
    "team_a_must_win": false,
    "team_b_must_win": false,
    "draw_benefits_team": "ninguno/A/B",
    "rest_days_team_a": 0,
    "rest_days_team_b": 0,
    "travel_fatigue_a": "bajo/medio/alto",
    "travel_fatigue_b": "bajo/medio/alto",
    "stage": "fase del torneo"
  }},
  "weather_stadium": {{
    "temperature_celsius": 20,
    "humidity_pct": 60,
    "rain_probability": 10,
    "wind_kmh": 15,
    "altitude_meters": 0,
    "pitch_condition": "bueno/regular/malo",
    "stadium_capacity": 0,
    "home_advantage_rating": 7.0,
    "notes": "notas clima/estadio"
  }},
  "referee": {{
    "name": "nombre si disponible",
    "yellow_cards_avg": 0.0,
    "red_cards_avg": 0.0,
    "penalties_per_game": 0.0,
    "fouls_per_game": 0.0,
    "style": "permisivo/normal/estricto",
    "notes": "observaciones relevantes"
  }},
  "psychological": {{
    "team_a_morale": "alto/medio/bajo",
    "team_b_morale": "alto/medio/bajo",
    "team_a_pressure": "descripción",
    "team_b_pressure": "descripción",
    "rivalry_factor": "bajo/medio/alto",
    "key_psychological_factor": "descripción del factor más importante"
  }},
  "news": {{
    "team_a_news": ["noticia relevante 1", "noticia relevante 2"],
    "team_b_news": ["noticia relevante 1", "noticia relevante 2"],
    "press_conference_notes": "declaraciones importantes",
    "internal_issues": "ninguno conocido o descripción",
    "confirmed_lineups": false
  }},
  "betting_market": {{
    "opening_odds_a": 0.0,
    "opening_odds_draw": 0.0,
    "opening_odds_b": 0.0,
    "current_odds_a": 0.0,
    "current_odds_draw": 0.0,
    "current_odds_b": 0.0,
    "odds_movement": "descripción del movimiento",
    "sharp_money_on": "A/empate/B/sin datos",
    "best_book_a": "casa - momio",
    "best_book_draw": "casa - momio",
    "best_book_b": "casa - momio",
    "implied_prob_a": 0.0,
    "implied_prob_draw": 0.0,
    "implied_prob_b": 0.0
  }},
  "mexican_odds": {{
    "playdoit": {{"home": 0.0, "draw": 0.0, "away": 0.0, "over_2_5": 0.0, "btts": 0.0, "available": true}},
    "caliente":  {{"home": 0.0, "draw": 0.0, "away": 0.0, "over_2_5": 0.0, "btts": 0.0, "available": true}},
    "codere":    {{"home": 0.0, "draw": 0.0, "away": 0.0, "over_2_5": 0.0, "btts": 0.0, "available": true}},
    "1xbet":     {{"home": 0.0, "draw": 0.0, "away": 0.0, "over_2_5": 0.0, "btts": 0.0, "available": true}},
    "best_value_pick": "descripción del mejor momio con más valor encontrado"
  }},
  "lambda_home": 1.5,
  "lambda_away": 1.2,
  "elo_home": 1800,
  "elo_away": 1750,
  "prediction_a": {{
    "basis": "estadístico",
    "winner": "A/empate/B",
    "confidence": 7,
    "reasoning": "explicación basada en datos y modelos",
    "key_stats": ["stat relevante 1", "stat relevante 2", "stat relevante 3"]
  }},
  "prediction_b": {{
    "basis": "contextual",
    "winner": "A/empate/B",
    "confidence": 6,
    "reasoning": "explicación basada en contexto, noticias y psicología",
    "key_factors": ["factor 1", "factor 2", "factor 3"]
  }},
  "final_prediction": {{
    "winner": "A/empate/B",
    "confidence_score": 7,
    "summary": "conclusión final comparando A y B",
    "main_risks": ["riesgo 1", "riesgo 2", "riesgo 3"],
    "value_bet": "descripción del valor encontrado si existe"
  }},
  "markets": {{
    "match_result": {{"pick": "A/empate/B", "confidence": 7, "reasoning": ""}},
    "double_chance": {{"pick": "A o empate / B o empate / A o B", "confidence": 8, "reasoning": ""}},
    "btts": {{"pick": "sí/no", "confidence": 7, "reasoning": ""}},
    "over_2_5": {{"pick": "sí/no", "confidence": 7, "reasoning": ""}},
    "under_2_5": {{"pick": "sí/no", "confidence": 6, "reasoning": ""}},
    "over_3_5": {{"pick": "sí/no", "confidence": 5, "reasoning": ""}},
    "cards_over_3_5": {{"pick": "sí/no", "confidence": 6, "reasoning": ""}},
    "corners_over_9_5": {{"pick": "sí/no", "confidence": 6, "reasoning": ""}},
    "scorer": {{"player": "nombre si hay valor claro", "type": "primer gol/cualquier momento", "confidence": 5, "reasoning": ""}}
  }},
  "parlays": {{
    "ultra_conservative": {{
      "name": "Ultra Conservador",
      "risk_level": 1,
      "selections": [
        {{"market": "nombre mercado", "pick": "selección", "odds": 1.30, "confidence": 9, "reasoning": "por qué", "risk": "riesgo principal"}}
      ],
      "combined_odds": 1.60,
      "expected_value": 0.15,
      "win_probability": 75.0,
      "strategy": "descripción de la estrategia conservadora"
    }},
    "conservative": {{
      "name": "Conservador",
      "risk_level": 3,
      "selections": [
        {{"market": "nombre mercado", "pick": "selección", "odds": 1.50, "confidence": 8, "reasoning": "por qué", "risk": "riesgo"}}
      ],
      "combined_odds": 2.50,
      "expected_value": 0.25,
      "win_probability": 55.0,
      "strategy": "descripción"
    }},
    "balanced": {{
      "name": "Balanceado",
      "risk_level": 5,
      "selections": [
        {{"market": "nombre mercado", "pick": "selección", "odds": 2.00, "confidence": 7, "reasoning": "por qué", "risk": "riesgo"}}
      ],
      "combined_odds": 5.00,
      "expected_value": 0.40,
      "win_probability": 35.0,
      "strategy": "descripción"
    }},
    "risky": {{
      "name": "Riesgoso",
      "risk_level": 8,
      "selections": [
        {{"market": "nombre mercado", "pick": "selección", "odds": 3.50, "confidence": 5, "reasoning": "por qué", "risk": "riesgo"}}
      ],
      "combined_odds": 15.00,
      "expected_value": 0.60,
      "win_probability": 12.0,
      "strategy": "descripción"
    }}
  }}
}}

IMPORTANTE: Busca datos reales actualizados en la web. Llena todos los campos con la mejor información disponible.
Si un dato no está disponible, usa estimaciones razonables basadas en el historial conocido del equipo/deporte.
Los lambda_home y lambda_away son los goles esperados por partido (o puntos/carreras según el deporte).
Para deportes no futbolísticos adapta los mercados apropiadamente."""
