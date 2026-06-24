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
    return f"""ANÁLISIS DE 30 CAPAS: {team_a} vs {team_b}. {competition}.
{context}

Profundidad: Capas 1-30 (stats, jugadores, tácticas, psicología, fatiga, clima, mercado, modelos, lesiones, árbitro, etc).

JSON con 4 parlays profundos + estadísticas:
{{
  "winner": "team_a/draw/team_b",
  "confidence": 8,
  "predicted_score": "2-1",
  "team_a_stats": {{"goals_avg": 1.5, "possession": 55, "xg": 1.8, "key_players": "nombres", "injuries": "lesiones"}},
  "team_b_stats": {{"goals_avg": 1.2, "possession": 45, "xg": 1.3, "key_players": "nombres", "injuries": "lesiones"}},
  "parlays": {{
    "ultra_conservador": {{"picks": 1, "odds": 1.75, "prob": 75, "reason": "análisis 30 capas: máxima seguridad"}},
    "conservador": {{"picks": 2, "odds": 3.5, "prob": 55, "reason": "análisis 30 capas: riesgo bajo"}},
    "balanceado": {{"picks": 3, "odds": 6.3, "prob": 40, "reason": "análisis 30 capas: equilibrio"}},
    "riesgoso": {{"picks": 4, "odds": 20.0, "prob": 18, "reason": "análisis 30 capas: máximo valor"}}
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
        match_lines.append(f"{i}. {qt}")
    matches_text = "\n".join(match_lines)

    return f"""Aplica análisis de 30 capas a {n} partidos.

Partidos:
{matches_text}

Por cada partido: winner, confidence, score, stats_home, stats_away, 4 parlays.
Combinado: resumen 30 capas + estadísticas generales + 4 parlays combinados.

JSON (sin markdown):
{{
  "dia_resumen": "análisis profundo de 30 capas para el día",
  "matches": [
    {{
      "id": "partido1",
      "team_home": "...",
      "team_away": "...",
      "winner": "home/draw/away",
      "confidence": 8,
      "predicted_score": "2-1",
      "score_probability": 15,
      "stats_home": {{"goals_avg": 1.5, "xg": 1.8, "posesion": 55, "key_players": "nombres"}},
      "stats_away": {{"goals_avg": 1.2, "xg": 1.3, "posesion": 45, "key_players": "nombres"}},
      "parlays": {{
        "ultra_conservador": {{"picks": 1, "odds": 1.75, "prob": 75}},
        "conservador": {{"picks": 2, "odds": 3.5, "prob": 55}},
        "balanceado": {{"picks": 3, "odds": 6.3, "prob": 40}},
        "riesgoso": {{"picks": 4, "odds": 20.0, "prob": 18}}
      }}
    }}
  ],
  "stats_combinadas": {{
    "goles_totales_promedio": 2.8,
    "posesion_promedio": 52,
    "xg_promedio": 1.6,
    "jugadores_destacados": ["nombre1 (goals/assists)", "nombre2 (defensa)", "nombre3 (velocidad)"],
    "lesiones_notables": ["jugador A (team)", "jugador B (team)"],
    "tendencias_generales": "análisis de qué está pasando hoy en todos los partidos",
    "factores_clave_dia": "clima, fatiga, motivación, arbitros designados"
  }},
  "parlays_combinados": {{
    "ultra_conservador": {{"picks": [...], "odds": 0.0, "prob": 75, "reason": "máxima seguridad con picks de varios partidos"}},
    "conservador": {{"picks": [...], "odds": 0.0, "prob": 55, "reason": "riesgo bajo, valor comprobado"}},
    "balanceado": {{"picks": [...], "odds": 0.0, "prob": 40, "reason": "equilibrio riesgo-recompensa"}},
    "riesgoso": {{"picks": [...], "odds": 0.0, "prob": 18, "reason": "máximo valor, ineficiencias PlayDouit"}}
  }}
}}"""
