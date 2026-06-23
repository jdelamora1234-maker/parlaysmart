SYSTEM_PROMPT = """Eres una Inteligencia Artificial Cuantitativa Avanzada especializada en prediccion deportiva y explotacion de ineficiencias de mercado, operando al nivel de fondos de cobertura deportiva (estilo Starlizard / Smartodds).

Tu metodologia procesa cada partido mediante 30 capas de micro-analisis independientes:

CAPAS 1-10 (DATOS DUROS):
1. Estadisticas colectivas: xG, xGA, PPDA, posesion por zona, tasa de corners, forma movil 5/10/20 partidos
2. Perfil individual de jugadores: metricas por 90min, riesgo disciplinario acumulado, indice de sobrecarga biometrica
3. Geometria tactica: morfologia de formacion, linea defensiva, dependencia de estrella (MVP Dependency)
4. Entrenadores: in-game management, historial especifico vs rival actual, estabilidad en el puesto
5. Psicologia colectiva: multiplicador de motivacion segun objetivo, resiliencia post-gol-en-contra, factor revancha
6. Noticias y sentimiento NLP: deudas salariales, conflictos vestuario, rumores de transferencia activos
7. Redes sociales 48h: contenido de jugadores clave (concentracion vs ocio), fugas de alineacion
8. Entorno familiar: disruptores emocionales (fallecimientos, divorcios, nacimientos recientes)
9. Fatiga y calendario: horas de descanso neto, congestion (partidos en 21 dias), jet lag por zonas horarias
10. Arbitro: tarjetas/partido, penaltis/partido, sesgo acustico en estadio lleno, historial con ambos clubs

CAPAS 11-20 (CONTEXTO):
11. Clima: temperatura, humedad (>75% reduce rendimiento aerobico -15% en 2a parte), viento >25km/h
12. Geografia: altitud del estadio (>2000msnm activa hipoxia en visitante desde min.60), distancia de traslado
13. Estadio: tipo de cesped (sintetico acelera balon, fatiga articular en visitantes), dimensiones, % ocupacion
14. Importancia: nivel 1-5 (final mundial=5, amistoso=1), ajusta intensidad defensiva y rotacion
15. Mercado: dropping odds >10% sin noticia = smart money, analisis de overround de Playdoit vs Asia
16. Metricas avanzadas: xA, Big Chances Created, Progressive Passes, Goals Prevented
17. Modelos propios: Poisson, Elo progresivo, Monte Carlo 10,000 iteraciones
18. Variables ocultas: clanes internos por idioma, apatia por contrato, bonos de directiva
19. Factores politicos: presion de patrocinadores sobre alineacion, auditoria federacion
20. Factores raros: hotel visitante (ruido nocturno), cambio de balon oficial, intoxicacion alimentaria

CAPAS 21-30 (INTELIGENCIA DE MERCADO):
21. Comportamiento gestual: lenguaje corporal en calentamiento, dinamica de celebraciones
22. Biometria: frecuencia cardiaca GPS en entrenamientos, HRV, velocidad de sprint comparada vs historico
23. Salud financiera: valor de plantilla, urgencia de vender jugadores para sanear presupuesto
24. Comunidad digital: hilos Reddit/foros, filtraciones de alineacion de periodistas acreditados
25. Ineficiencias Playdoit: latencia de cuotas live >3 segundos, prop bets mal calculadas por promedios estaticos
26. Value bets: sesgo del aficionado (America, Chivas, Real Madrid), correlacion cruzada inversa
27. Ingenieria inversa: cuota de apertura como input predictivo, analisis del margen overround
28. Anti-limbo live: indice de peligro inminente (posicion del balon), timing optimo de envio de ticket
29. Gestion de stake fraccionado: evitar limitacion de cuenta, distribucion en mercados combinados
30. Efecto VAR: parones >180 segundos penalizan ritmo -20% en siguientes 10 minutos (oportunidad en bajas live)

DIRECTIVA CRITICA DE MERCADO:
- PlayDouit (playdoit.mx) es la casa PRIMARIA. Todos los momios de parlays y selecciones deben ser de PlayDouit.
- Detecta cuando el sesgo del aficionado ha inflado una cuota de PlayDouit: calcula la probabilidad real con Monte Carlo y compara con la cuota implicita de PlayDouit. Si la cuota implicita es >8% mayor que la probabilidad real, es una value bet confirmada con EV+.
- Busca dropping odds: si PlayDouit abre en 1.80 y baja a 1.55 sin noticias publicas, hay smart money.

REGLA DE OUTPUT:
Tu respuesta final es UNICAMENTE el objeto JSON solicitado. Cero texto introductorio, cero markdown, cero explicaciones fuera del JSON. Razona internamente. Salida: solo { ... }."""


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
    if query:
        header = f"""El usuario quiere analizar: "{query}"
Identifica automaticamente: equipo local, visitante, deporte, competicion y fecha.
Aplica las 30 capas de micro-analisis. Usa esos datos en "match_info"."""
    else:
        header = f"""PARTIDO: {team_a} vs {team_b}
DEPORTE: {sport} | COMPETICION: {competition} | FECHA: {date_str}
{f'CONTEXTO: {context}' if context else ''}
Aplica las 30 capas de micro-analisis del protocolo."""

    return f"""{header}

INSTRUCCIONES:
- Analiza TODAS las 30 capas de micro-analisis
- Usa tu conocimiento sobre estadísticas, tácticas, psicología, mercado
- Los momios reales están en el contexto (The Odds API) — úsalos para detectar value bets
- Calcula probabilidades con Poisson, Monte Carlo, Elo
- Genera estadísticas comparativas EXACTO (como Sofascore)

Devuelve UNICAMENTE este JSON (sin markdown, sin texto extra, SIN parlays en esta etapa):

{{
  "match_info": {{
    "team_a": "{team_a}",
    "team_b": "{team_b}",
    "sport": "{sport}",
    "competition": "{competition}",
    "date": "{date_str}"
  }},
  "stats_comparison": [
    {{"metric": "Ball possession %", "team_a": 0.0, "team_b": 0.0}},
    {{"metric": "Expected goals (xG)", "team_a": 0.0, "team_b": 0.0}},
    {{"metric": "Big chances", "team_a": 0, "team_b": 0}},
    {{"metric": "Total shots", "team_a": 0, "team_b": 0}},
    {{"metric": "Shots on target", "team_a": 0, "team_b": 0}},
    {{"metric": "Goalkeeper saves", "team_a": 0, "team_b": 0}},
    {{"metric": "Corner kicks", "team_a": 0, "team_b": 0}},
    {{"metric": "Fouls committed", "team_a": 0, "team_b": 0}},
    {{"metric": "Pass accuracy %", "team_a": 0.0, "team_b": 0.0}},
    {{"metric": "Tackles", "team_a": 0, "team_b": 0}},
    {{"metric": "Interceptions", "team_a": 0, "team_b": 0}},
    {{"metric": "Offsides", "team_a": 0, "team_b": 0}}
  ],
  "stats_team_a": {{
    "goals_scored_avg": 0.0,
    "goals_conceded_avg": 0.0,
    "xg_avg": 0.0,
    "xga_avg": 0.0,
    "shots_per_game": 0.0,
    "shots_on_target_per_game": 0.0,
    "possession_avg": 0.0,
    "corners_per_game": 0.0,
    "yellow_cards_avg": 0.0,
    "red_cards_avg": 0.0,
    "fouls_per_game": 0.0,
    "ppda": 0.0,
    "home_record": "W-D-L",
    "away_record": "W-D-L",
    "season_record": "W-D-L",
    "points_per_game": 0.0,
    "league_position": 0,
    "last_5": ["W","W","D","L","W"],
    "last_5_goals_scored": [0,0,0,0,0],
    "last_5_goals_conceded": [0,0,0,0,0],
    "clean_sheets_pct": 0.0,
    "btts_rate": 0.0,
    "over_2_5_rate": 0.0,
    "over_1_5_rate": 0.0,
    "first_goal_rate": 0.0,
    "comeback_rate": 0.0,
    "avg_goals_first_half": 0.0,
    "avg_goals_second_half": 0.0,
    "form_rating": 0.0,
    "current_streak": "descripcion",
    "injury_impact": "alto/medio/bajo",
    "tactical_system": "4-3-3",
    "attacking_style": "descripcion breve",
    "star_player": "nombre",
    "mvp_dependency_pct": 0.0,
    "motivation_multiplier": 1.0,
    "fatigue_index": 0
  }},
  "stats_team_b": {{
    "goals_scored_avg": 0.0,
    "goals_conceded_avg": 0.0,
    "xg_avg": 0.0,
    "xga_avg": 0.0,
    "shots_per_game": 0.0,
    "shots_on_target_per_game": 0.0,
    "possession_avg": 0.0,
    "corners_per_game": 0.0,
    "yellow_cards_avg": 0.0,
    "red_cards_avg": 0.0,
    "fouls_per_game": 0.0,
    "ppda": 0.0,
    "home_record": "W-D-L",
    "away_record": "W-D-L",
    "season_record": "W-D-L",
    "points_per_game": 0.0,
    "league_position": 0,
    "last_5": ["W","L","W","W","D"],
    "last_5_goals_scored": [0,0,0,0,0],
    "last_5_goals_conceded": [0,0,0,0,0],
    "clean_sheets_pct": 0.0,
    "btts_rate": 0.0,
    "over_2_5_rate": 0.0,
    "over_1_5_rate": 0.0,
    "first_goal_rate": 0.0,
    "comeback_rate": 0.0,
    "avg_goals_first_half": 0.0,
    "avg_goals_second_half": 0.0,
    "form_rating": 0.0,
    "current_streak": "descripcion",
    "injury_impact": "alto/medio/bajo",
    "tactical_system": "4-4-2",
    "attacking_style": "descripcion breve",
    "star_player": "nombre",
    "mvp_dependency_pct": 0.0,
    "motivation_multiplier": 1.0,
    "fatigue_index": 0
  }},
  "head_to_head": {{
    "total_meetings": 0,
    "team_a_wins": 0,
    "draws": 0,
    "team_b_wins": 0,
    "avg_goals_per_game": 0.0,
    "last_5_h2h": [
      {{"date":"YYYY-MM-DD","home":"equipo","away":"equipo","score":"0-0","competition":"liga"}},
      {{"date":"YYYY-MM-DD","home":"equipo","away":"equipo","score":"0-0","competition":"liga"}},
      {{"date":"YYYY-MM-DD","home":"equipo","away":"equipo","score":"0-0","competition":"liga"}}
    ],
    "last_3_results": ["desc 1","desc 2","desc 3"],
    "notable_pattern": "descripcion de patron",
    "btts_in_h2h": 0,
    "over_2_5_in_h2h": 0,
    "trend": "descripcion de tendencia",
    "tactical_tendency": "tiende a cerrado/abierto cuando estos tecnicos se cruzan"
  }},
  "players": {{
    "key_player_a": "nombre y stats clave",
    "key_player_b": "nombre y stats clave",
    "suspensions_a": "suspendidos o ninguno",
    "suspensions_b": "suspendidos o ninguno",
    "injuries_a": "lesionados importantes o ninguno",
    "injuries_b": "lesionados importantes o ninguno",
    "discipline_risk_a": "jugadores cerca de suspension por acumulacion",
    "discipline_risk_b": "jugadores cerca de suspension por acumulacion",
    "fatigue_risk_a": "jugadores con sobrecarga de minutos",
    "fatigue_risk_b": "jugadores con sobrecarga de minutos"
  }},
  "context": {{
    "home_advantage": "alto/medio/bajo con justificacion",
    "travel_fatigue": "descripcion del desgaste por viaje",
    "rivalry_level": "clasico/alto/medio/bajo",
    "importance": "alta/media/baja y por que",
    "recent_momentum": "momento actual de ambos equipos",
    "tournament_level": 3,
    "tournament_level_desc": "descripcion del nivel 1-5"
  }},
  "weather_stadium": {{
    "temp_celsius": 0,
    "humidity_pct": 0,
    "wind_kmh": 0,
    "rain_prob_pct": 0,
    "weather": "soleado/nublado/lluvia/nieve",
    "stadium": "nombre del estadio",
    "altitude_msnm": 0,
    "capacity": 0,
    "occupancy_pct": 0,
    "field_type": "natural/hibrido/sintetico",
    "field_condition": "excelente/buena/regular/mala"
  }},
  "referee": {{
    "name": "nombre del arbitro",
    "yellow_cards_avg": 0.0,
    "red_cards_avg": 0.0,
    "penalty_rate": 0.0,
    "var_overturn_rate": 0.0,
    "home_bias": "descripcion de sesgo si existe"
  }},
  "psychological": {{
    "pressure_a": "descripcion presion equipo A",
    "pressure_b": "descripcion presion equipo B",
    "motivation_a": "alta/media/baja con razon",
    "motivation_b": "alta/media/baja con razon",
    "mental_edge": "team_a/team_b/neutral",
    "locker_room_a": "cohesion o conflictos internos",
    "locker_room_b": "cohesion o conflictos internos",
    "revenge_factor": "descripcion o ninguno",
    "external_pressure": "presion mediatica, directiva, etc."
  }},
  "news": {{
    "team_a": "noticias relevantes ultimas 48h",
    "team_b": "noticias relevantes ultimas 48h",
    "general": "contexto adicional relevante",
    "social_media_alerts": "senales de redes sociales relevantes"
  }},
  "tactical_desequilibrium": {{
    "zone_advantage_a": "zonas donde A supera geometricamente a B",
    "zone_advantage_b": "zonas donde B supera geometricamente a A",
    "key_duel": "duelo individual critico que decidira el partido",
    "setpiece_edge": "quien domina balones parados y por que",
    "pressing_trap": "zona del campo donde se generara la mayor recuperacion de balon",
    "counterattack_risk": "vulnerabilidad especifica al contraataque"
  }},
  "gamestate_simulation": {{
    "scenario_draw": "cronologia proyectada si el partido se mantiene 0-0 hasta min.60",
    "scenario_home_early_goal": "comportamiento proyectado si local anota en primeros 20 min",
    "scenario_away_early_goal": "comportamiento proyectado si visitante anota en primeros 20 min",
    "critical_minutes": "ventanas de tiempo de mayor probabilidad de gol",
    "second_half_shift": "que cambia tactica y fisicamente en la segunda parte"
  }},
  "betting_market": {{
    "consensus_pick": "pick que la mayoria del mercado favorece",
    "line_movement": "descripcion del movimiento de lineas",
    "sharp_money": "donde esta el dinero inteligente",
    "public_bias": "sesgo del aficionado detectado",
    "value_bet": "descripcion de la apuesta de valor",
    "dropping_odds_alert": "caida de cuotas >10% detectada o ninguna",
    "overround_playdoit": 0.0
  }},
  "mexican_odds": {{
    "playdouit_home": 0.0,
    "playdouit_draw": 0.0,
    "playdouit_away": 0.0,
    "playdouit_over_2_5": 0.0,
    "playdouit_under_2_5": 0.0,
    "playdouit_btts_yes": 0.0,
    "playdouit_btts_no": 0.0,
    "caliente_home": 0.0,
    "caliente_draw": 0.0,
    "caliente_away": 0.0,
    "1xbet_home": 0.0,
    "1xbet_draw": 0.0,
    "1xbet_away": 0.0,
    "best_value": "descripcion del mejor valor disponible en PlayDouit"
  }},
  "playdoit_inefficiency": {{
    "detected": true,
    "market": "mercado especifico mal calculado",
    "playdoit_odds": 0.0,
    "true_odds": 0.0,
    "ev_pct": 0.0,
    "reason": "por que PlayDouit tiene este mercado mal calculado (sesgo de aficionado, correlacion cruzada, etc.)"
  }},
  "diagnostic_table": {{
    "prob_home_true": 0.0,
    "prob_draw_true": 0.0,
    "prob_away_true": 0.0,
    "true_xg_total": 0.0,
    "fatigue_delta": 0,
    "chaos_index": 5,
    "chaos_reasons": "factores que elevan la impredecibilidad",
    "playdoit_inefficiency_market": "mercado / cuota local",
    "value_edge_market": "mercado con mayor EV+",
    "value_edge_min_odds": 0.0
  }},
  "live_triggers": [
    {{
      "trigger": "evento especifico en vivo (ej: gol local en min.1-20)",
      "action": "apuesta recomendada en PlayDouit live",
      "market": "mercado especifico",
      "reasoning": "por que este evento dispara esta oportunidad"
    }},
    {{
      "trigger": "segundo evento especifico",
      "action": "accion en live",
      "market": "mercado",
      "reasoning": "razon"
    }},
    {{
      "trigger": "tercer evento (ej: VAR revision >180 seg en min.30-75)",
      "action": "apostar bajas de goles o no-corners a corto plazo",
      "market": "bajas siguientes 10 min",
      "reasoning": "efecto VAR: enfriamiento fisico y cognitivo de jugadores"
    }}
  ],
  "markets": {{
    "btts": {{"prob": 0.0, "odds": 0.0, "recommendation": "si/no/evitar"}},
    "over_2_5": {{"prob": 0.0, "odds": 0.0, "recommendation": "si/no/evitar"}},
    "over_1_5": {{"prob": 0.0, "odds": 0.0, "recommendation": "si/no/evitar"}},
    "corners_over_9": {{"prob": 0.0, "odds": 0.0, "recommendation": "si/no/evitar"}},
    "home_win": {{"prob": 0.0, "odds": 0.0, "recommendation": "si/no/evitar"}},
    "draw": {{"prob": 0.0, "odds": 0.0, "recommendation": "si/no/evitar"}},
    "away_win": {{"prob": 0.0, "odds": 0.0, "recommendation": "si/no/evitar"}},
    "double_chance_1x": {{"prob": 0.0, "odds": 0.0, "recommendation": "si/no/evitar"}},
    "double_chance_x2": {{"prob": 0.0, "odds": 0.0, "recommendation": "si/no/evitar"}}
  }},
  "final_prediction": {{
    "winner": "team_a/draw/team_b",
    "confidence": 7,
    "score": "2-1",
    "reasoning": "razonamiento detallado de 4-6 oraciones integrando las 30 capas",
    "key_factors": ["factor 1 con datos", "factor 2 con datos", "factor 3 con datos"],
    "risks": ["riesgo 1 cuantificado", "riesgo 2 cuantificado"],
    "best_bet": "el mercado especifico con mayor EV+ en PlayDouit",
    "avoid": "que evitar en este partido y por que"
  }},
  "lambda_home": 1.4,
  "lambda_away": 1.1,
  "elo_home": 1700,
  "elo_away": 1650
}}"""


def build_today_matches_prompt(date_str):
    return f"""Busca con Google Search todos los partidos de futbol confirmados para el dia {date_str} en las competiciones mas importantes.

IMPORTANTE: La hora debe ser en hora de Mexico (UTC-6, zona Centro, permanente). Mexico ya no cambia horario.

BUSCAR OBLIGATORIAMENTE:
- Mundial FIFA 2026 (si esta activo) — todos los partidos del dia, con grupo y sede
- UEFA Champions League / Europa League / Conference League
- Premier League, La Liga, Bundesliga, Serie A, Ligue 1
- Liga MX (Apertura/Clausura), Copa MX
- MLS
- Copa Libertadores, Copa Sudamericana
- Copa America, CONCACAF Champions

Solo incluye ligas con partidos reales ese dia. Si no hay partidos de una liga, no la incluyas.

Devuelve UNICAMENTE este JSON valido (sin markdown, sin texto extra):

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
