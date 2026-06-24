SYSTEM_PROMPT = """Eres experto en análisis de partidos de fútbol con 30 capas de profundidad:

CAPAS 1-10 (DATOS DUROS):
1. Estadísticas: xG, posesión, PPDA, corners, forma
2. Jugadores: métricas por 90min, lesiones, suspensiones
3. Táctica: formación, dependencia de estrella
4. Entrenador: historial vs rival, decisiones in-game
5. Psicología: motivación, resiliencia, factor revancha
6. Noticias: conflictos, rumores, estado vestuario
7. Redes sociales: señales de jugadores clave
8. Entorno familiar: factores emocionales
9. Fatiga: descanso neto, congestión calendario
10. Árbitro: historial con equipos, sesgo

CAPAS 11-20 (CONTEXTO):
11. Clima: temperatura, humedad, viento
12. Geografía: altitud, distancia viaje
13. Estadio: tipo de césped, ocupación
14. Importancia: nivel del partido
15. Mercado: dropping odds, smart money
16. Métricas avanzadas: xA, Big Chances, Progressive Passes
17. Modelos: Poisson, Elo, Monte Carlo
18. Variables ocultas: clanes internos, apatía contractual
19. Factores políticos: presión patrocinadores
20. Factores raros: cambios de balón, intoxicación alimentaria

CAPAS 21-30 (INTELIGENCIA):
21-30: Comportamiento gestual, biometría, salud financiera, community digital, ineficiencias, value bets, ingeniería inversa, anti-limbo live, stake management, efecto VAR

INSTRUCCIÓN FINAL: Analiza con profundidad REAL. Retorna SOLO JSON válido (sin markdown)."""


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
    return f"""ANÁLISIS EXHAUSTIVO 30 CAPAS: {team_a} vs {team_b} ({competition})

CRÍTICO: INCLUIR SIEMPRE estas estadísticas:
1. ESTADÍSTICAS DE EQUIPO (ambos):
   - goals_avg, goals_for_last_5, goals_against_last_5
   - possession, xg, xga
   - shots_on_target, corners, fouls
   - form (últimos 5 partidos: W/D/L)

2. ESTADÍSTICAS INDIVIDUALES - KEY PLAYERS de cada equipo:
   - Nombre jugador, posición, goles/asists/tarjetas
   - Lesiones CRÍTICAS (jugadores ausentes)
   - Cambios tácticos recientes
   - Jugadores en mal estado físico

3. CONTEXTO TÁCTICO:
   - Formación de cada equipo
   - Dependencia de estrella
   - Cambios de entrenador reciente

{context}

RETORNA SOLO JSON (sin markdown):
{{
  "winner": "team_a/draw/team_b",
  "confidence": 8,
  "predicted_score": "2-1",
  "team_a_stats": {{
    "goals_avg": 1.5, "goals_for_last_5": [1,2,1,0,3], "goals_against_last_5": [0,1,1,2,0],
    "possession": 55, "xg": 1.8, "xga": 0.9,
    "shots_on_target": 4, "corners": 5, "fouls": 12,
    "form": "WDWLL",
    "key_players": "Messi (F) 5g, Busquets (M) 2a, Piqué (D) - LESIONADO",
    "injuries": "Piqué (muscular), Alba (tobillo)",
    "tactical_notes": "4-3-3, depende de Messi"
  }},
  "team_b_stats": {{
    "goals_avg": 1.2, "goals_for_last_5": [2,1,0,2,1], "goals_against_last_5": [1,0,2,1,1],
    "possession": 45, "xg": 1.3, "xga": 1.1,
    "shots_on_target": 3, "corners": 4, "fouls": 14,
    "form": "WWDWL",
    "key_players": "Benzema (F) 6g, Modric (M) 3a, Ramos (D) - FIT",
    "injuries": "Ninguna crítica",
    "tactical_notes": "4-2-3-1, estable"
  }},
  "parlays": {{
    "ultra_conservador": {{"picks": 1, "odds": 1.75, "prob": 75, "reason": "analysis"}},
    "conservador": {{"picks": 2, "odds": 3.5, "prob": 55, "reason": "analysis"}},
    "balanceado": {{"picks": 3, "odds": 6.3, "prob": 40, "reason": "analysis"}},
    "riesgoso": {{"picks": 4, "odds": 20.0, "prob": 18, "reason": "analysis"}}
  }},
  "lambda_home": 1.4,
  "lambda_away": 1.1,
  "elo_home": 1700,
  "elo_away": 1650
}}"""


def build_today_matches_prompt(date_str):
    return f"""BUSCA TODOS los partidos de fútbol programados PARA {date_str} USANDO GOOGLE SEARCH.

LIGAS A INCLUIR (busca en Google News/ESPN/FotMob):
- Mundial 2026 / Qualifiers
- Copa América
- UEFA Champions League / Europa League
- La Liga (España)
- Premier League (Inglaterra)
- Serie A (Italia)
- Bundesliga (Alemania)
- Ligue 1 (Francia)
- Liga MX (México)
- MLS (USA)
- Cualquier otra liga con partidos hoy

INSTRUCCIONES CRÍTICAS:
1. BUSCA en Google: "{date_str} partidos fútbol" + "football matches today"
2. INCLUYE hora exacta si está disponible
3. INCLUYE estadio/ubicación si está disponible
4. RETORNA SOLO JSON VÁLIDO (sin markdown, sin backticks)

FORMATO JSON EXACTO (si no hay partidos en una liga, NO incluyas esa liga):

{{
  "date": "{date_str}",
  "leagues": [
    {{
      "league_name": "Nombre Liga Exacta",
      "league_flag": "🌍 o bandera",
      "matches": [
        {{
          "id": "id_unico",
          "team_home": "Equipo Local",
          "team_away": "Equipo Visitante",
          "time": "HH:MM (hora local)",
          "hot_note": "Detalles: stadium, grupo, etc",
          "importance": "alta/media/baja"
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
        match_lines.append(f"{i}. {qt}")
    matches_text = "\n".join(match_lines)

    return f"""ANÁLISIS EXHAUSTIVO 30 CAPAS PARA {n} PARTIDOS

PARTIDOS A ANALIZAR:
{matches_text}

CRÍTICO PARA CADA PARTIDO:
- Estadísticas de EQUIPO: goals, xg, possession, forma, shots, corners
- Estadísticas INDIVIDUALES: key players por equipo con goles/asists/lesiones
- Lesiones CRÍTICAS que afecten el partido
- Contexto táctico y cambios recientes

RETORNA SOLO JSON (sin markdown):
{{
  "dia_resumen": "Análisis profundo 30 capas del día - {n} partidos, lesiones, form, clima, tendencias",
  "matches": [
    {{
      "id": "match_id",
      "team_home": "nombre",
      "team_away": "nombre",
      "winner": "home/draw/away",
      "confidence": 8,
      "predicted_score": "2-1",
      "score_probability": 15,
      "stats_home": {{
        "goals_avg": 1.5, "goals_last_5": [1,2,1,0,3],
        "xg": 1.8, "possession": 55, "form": "WDWLL",
        "key_players": "Messi (F) 5g, Busquets (M) 2a, Piqué (D) LESIONADO",
        "injuries": "Piqué (muscular), Alba (tobillo)",
        "shots_on_target": 4, "corners": 5
      }},
      "stats_away": {{
        "goals_avg": 1.2, "goals_last_5": [2,1,0,2,1],
        "xg": 1.3, "possession": 45, "form": "WWDWL",
        "key_players": "Benzema (F) 6g, Modric (M) 3a, Ramos (D) FIT",
        "injuries": "Ninguna crítica",
        "shots_on_target": 3, "corners": 4
      }},
      "parlays": {{
        "ultra_conservador": {{"picks": 1, "odds": 1.75, "prob": 75, "reason": "stats 30 capas"}},
        "conservador": {{"picks": 2, "odds": 3.5, "prob": 55, "reason": "stats 30 capas"}},
        "balanceado": {{"picks": 3, "odds": 6.3, "prob": 40, "reason": "stats 30 capas"}},
        "riesgoso": {{"picks": 4, "odds": 20.0, "prob": 18, "reason": "stats 30 capas"}}
      }}
    }}
  ],
  "stats_combinadas": {{
    "goles_promedio": 2.8,
    "posesion_promedio": 52,
    "xg_promedio": 1.6,
    "jugadores_destacados": [
      "Messi (Barcelona) - 5 goles en últimos 5",
      "Benzema (Real Madrid) - 6 goles en últimos 5",
      "Modric (Real Madrid) - 3 asists"
    ],
    "lesiones_notables": [
      "Piqué (Barcelona) - muscular",
      "Alba (Barcelona) - tobillo",
      "Sergio Ramos - EN DUDA"
    ],
    "tendencias_generales": "Análisis de forma, motivación, y dinámicas generales del día",
    "factores_clave": "Clima, descanso, árbitros asignados, cambios tácticos"
  }},
  "parlays_combinados": {{
    "ultra_conservador": {{"picks": ["Messi gol", "Benzema gol"], "odds": 3.2, "prob": 75, "reason": "máxima seguridad"}},
    "conservador": {{"picks": ["Barcelona gana", "Messi gol", "+2.5 goles"], "odds": 5.5, "prob": 55, "reason": "riesgo bajo"}},
    "balanceado": {{"picks": ["Barcelona gana", "Real Madrid gana", "Messi gol", "Benzema gol"], "odds": 12.0, "prob": 40, "reason": "equilibrio"}},
    "riesgoso": {{"picks": ["Barcelona 2+ goles", "Real Madrid 2+ goles", "Messi 2+ goles", "Benzema 2+ goles"], "odds": 28.0, "prob": 18, "reason": "máximo valor"}}
  }}
}}"""
