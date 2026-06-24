SYSTEM_PROMPT = """ERES EXPERTO EN ANÁLISIS DE PARTIDOS DE FÚTBOL - 30 CAPAS ESTRUCTURADAS

TU TAREA: Analizar CADA CAPA explícitamente. No asumir. No saltear. PROFUNDIDAD REAL.

═══ CAPAS 1-10: ANÁLISIS DURO (STATS + EQUIPOS) ═══
1️⃣ ESTADÍSTICAS OFENSIVAS: xG, goles/partido, posesión %, tiros al arco
2️⃣ ESTADÍSTICAS DEFENSIVAS: xGA, goles contra, presión, interceptos
3️⃣ JUGADORES CLAVE: Top scorer + asists, lesionados críticos, suspendidos
4️⃣ FORMACIÓN TÁCTICA: Sistema (4-3-3, 3-5-2, etc), dependencia de estrella (Messi/Mbappé?)
5️⃣ ENTRENADOR: Historial HEAD-TO-HEAD vs rival, cambios tácticos recientes, decisiones in-game
6️⃣ PSICOLOGÍA: Motivación (playoff/descenso?), resiliencia, revancha vs rival
7️⃣ NOTICIAS: Conflictos vestuario, rumores transferencia, estado emocional del equipo
8️⃣ PRESIÓN MEDIÁTICA: Expectativas, apoyo de afición, presión en jugadores
9️⃣ FATIGA: Descanso desde último partido (3 días? 1 día?), calendario congestionado
🔟 ÁRBITRO: Historial con los equipos, sesgo (favorece local 60%?), tarjetas/decisiones

═══ CAPAS 11-20: CONTEXTO (AMBIENTE + MERCADO) ═══
1️⃣1️⃣ CLIMA: Temperatura, humedad, viento (favorece posesión o contraataque?)
1️⃣2️⃣ GEOGRAFÍA: Altitud (favorece equipo local?), viaje largo (jet lag?)
1️⃣3️⃣ ESTADIO: Césped (favorece juego aéreo?), ocupación (local juega mejor en casa)
1️⃣4️⃣ IMPORTANCIA: ¿Playoff? ¿Descenso? ¿Duda? (afecta mentalidad)
1️⃣5️⃣ MERCADO: Odds actuales, smart money (donde va dinero inteligente?), dropping odds
1️⃣6️⃣ MÉTRICAS AVANZADAS: xA (asists esperados), Big Chances, Progressive Passes
1️⃣7️⃣ MODELOS MATEMÁTICOS: Poisson (goles esperados), ELO (rating), Monte Carlo (simulaciones)
1️⃣8️⃣ HEAD-TO-HEAD: Últimos 10 enfrentamientos (ganar %, promedio goles)
1️⃣9️⃣ FORMA CASA/FUERA: ¿Equipo juega diferente en casa? (varianza % ganancia)
2️⃣0️⃣ VARIABLES OCULTAS: Clanes internos, motivación contractual, amistades/rivalidades

═══ CAPAS 21-30: INTELIGENCIA AVANZADA ═══
2️⃣1️⃣ ANÁLISIS GESTUAL: Lenguaje corporal, confianza de jugadores
2️⃣2️⃣ BIOMETRÍA: Ritmo cardíaco en presión, fatiga física visible
2️⃣3️⃣ SALUD FINANCIERA: ¿Equipo en crisis económica? (rinde peor)
2️⃣4️⃣ COMMUNITY DIGITAL: Sentimiento en redes (confianza/miedo?)
2️⃣5️⃣ INEFICIENCIAS: Mercado valora mal algo? (OPORTUNIDAD)
2️⃣6️⃣ VALUE BETS: Odd 2.5 pero probabilidad 70% = VALUE positivo
2️⃣7️⃣ INGENIERÍA INVERSA: Si mercado da 60%, ¿qué sabe que yo no?
2️⃣8️⃣ FACTOR VAR: ¿Equipo favoritismo con árbitro?
2️⃣9️⃣ STAKE MANAGEMENT: Kelly Criterion para dimensionar apuesta
3️⃣0️⃣ SÍNTESIS FINAL: Combina TODAS las capas en SCORE ÚNICO

INSTRUCCIÓN CRÍTICA:
- Analiza CADA capa. SÍ o NO. Dato específico. No "probablemente" o "quizás"
- Para cada capa: [DATO] → [IMPACTO EN RESULTADO] → [% CONFIANZA]
- Los 4 parlays son RESULTADO directo de capas 21-30, no independientes
- JSON con análisis, NO markdown
"""


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
    return f"""╔════════════════════════════════════════════════════════════╗
║ ANÁLISIS 30 CAPAS: {team_a} vs {team_b} ({competition})
║ Profundidad: MÁXIMA | Estructura: 30 CAPAS EXPLÍCITAS
╚════════════════════════════════════════════════════════════╝

DATOS CONTEXTO (para referencias):
{context}

═══════════════════════════════════════════════════════════
ANÁLISIS ESTRUCTURA: APLICA LAS 30 CAPAS SISTEMÁTICAMENTE
═══════════════════════════════════════════════════════════

PASO 1: ANALIZA CAPAS 1-10 (DATOS DUROS)
├─ Capa 1️⃣: Stats ofensivas ({team_a} vs {team_b}): xG, goles/partido, posesión
├─ Capa 2️⃣: Stats defensivas: xGA, goles contra, presión
├─ Capa 3️⃣: Jugadores clave: Top scorer + lesiones críticas
├─ Capa 4️⃣: Formación táctica: Sistema + dependencia de estrella
├─ Capa 5️⃣: Entrenador: H2H vs rival + cambios recientes
├─ Capa 6️⃣: Psicología: Motivación + resiliencia
├─ Capa 7️⃣: Noticias: Conflictos, rumores, estado vestuario
├─ Capa 8️⃣: Presión mediática: Expectativas + apoyo afición
├─ Capa 9️⃣: Fatiga: Descanso desde último partido
└─ Capa 🔟: Árbitro: Historial + sesgo

PASO 2: ANALIZA CAPAS 11-20 (CONTEXTO)
├─ Capa 1️⃣1️⃣: Clima: Temperatura + impacto en juego
├─ Capa 1️⃣2️⃣: Geografía: Altitud + viaje + jet lag
├─ Capa 1️⃣3️⃣: Estadio: Césped + ocupación + ventaja local
├─ Capa 1️⃣4️⃣: Importancia: Playoff/descenso/amistoso
├─ Capa 1️⃣5️⃣: Mercado: Odds actuales + smart money
├─ Capa 1️⃣6️⃣: Métricas avanzadas: xA + Big Chances + Progressive Passes
├─ Capa 1️⃣7️⃣: Modelos: Poisson + ELO + Monte Carlo
├─ Capa 1️⃣8️⃣: Head-to-head: Últimos 10 + estadísticas H2H
├─ Capa 1️⃣9️⃣: Forma casa/fuera: % ganancia casa vs fuera
└─ Capa 2️⃣0️⃣: Variables ocultas: Clanes + motivación contractual

PASO 3: ANALIZA CAPAS 21-30 (SÍNTESIS INTELIGENTE)
├─ Capa 2️⃣1️⃣: Comportamiento gestual: Confianza de jugadores
├─ Capa 2️⃣2️⃣: Biometría: Fatiga visible + estado físico
├─ Capa 2️⃣3️⃣: Salud financiera: ¿Equipo en crisis?
├─ Capa 2️⃣4️⃣: Community digital: Sentimiento en redes
├─ Capa 2️⃣5️⃣: Ineficiencias mercado: ¿Valor no visto?
├─ Capa 2️⃣6️⃣: VALUE BETS: Odd vs probabilidad real
├─ Capa 2️⃣7️⃣: Ingeniería inversa: ¿Qué sabe mercado?
├─ Capa 2️⃣8️⃣: Factor VAR: Favoritismo arbitral
├─ Capa 2️⃣9️⃣: Stake management: Kelly Criterion
└─ Capa 3️⃣0️⃣: SÍNTESIS: Combina TODO → SCORE FINAL

═══════════════════════════════════════════════════════════
ESTRUCTURA JSON (refleja cada capa)
═══════════════════════════════════════════════════════════

{{
  "analisis_30_capas": {{
    "capas_1_10": {{
      "stats_ofensivas": {{"xg_home": 1.8, "goles_avg_home": 1.5, "posesion": 55}},
      "stats_defensivas": {{"xga_home": 0.9, "goles_contra_avg": 0.5}},
      "jugadores_clave": "Messi (5g, 2a) LESIÓN MUSCULAR",
      "formacion": "4-3-3, depende de Messi",
      "entrenador_h2h": "Gana 60% vs este rival",
      "psicologia": "Motivación ALTA (playoff)",
      "noticias": "Conflicto menor, resuelto",
      "presion_mediatica": "ALTA - expectativas máximas",
      "fatiga": "Descansó 3 días - ÓPTIMO",
      "arbitro": "Sesgo local 55%"
    }},
    "capas_11_20": {{
      "clima": "28°C, favorece posesión",
      "geografia": "500m, favorece local",
      "estadio": "Césped bueno, ocupación 80%",
      "importancia": "PLAYOFF - máxima presión",
      "mercado": "Odd 2.2, smart money en local",
      "metricas_avanzadas": "xA 1.2, Big Chances 3",
      "modelos": "Poisson: 70% local, ELO: 65%, MC: 68%",
      "h2h": "Últimos 10: 6W-2D-2L, 2.1 goles/partido",
      "forma_casa_fuera": "Casa: 75% ganancia, Fuera: 45%",
      "variables_ocultas": "Motivación contractual ALTA"
    }},
    "capas_21_30": {{
      "comportamiento": "Confianza ALTA en ambos",
      "biometria": "Fatiga baja, estado físico ÓPTIMO",
      "salud_financiera": "Estable",
      "community": "Sentimiento POSITIVO en redes",
      "ineficiencias": "Mercado subestima a local",
      "value_bets": "Odd 2.2 vs probabilidad 70% = VALUE +22%",
      "ingenieria_inversa": "Mercado protege al visitante (dinero inteligente allá)",
      "var": "Árbitro favor local, pero equilibrado",
      "kelly": "Stake 3-5% del presupuesto",
      "sintesis_final": "CONFIANZA 85% - Local gana"
    }}
  }},
  "prediccion_final": {{
    "winner": "team_a",
    "confidence": 85,
    "predicted_score": "2-1",
    "razon": "30 capas: stats superiores + H2H + psicología + valor mercado"
  }},
  "team_a_stats": {{
    "goals_avg": 1.5, "goals_for_last_5": [1,2,1,0,3], "goals_against_last_5": [0,1,1,2,0],
    "possession": 55, "xg": 1.8, "xga": 0.9, "shots_on_target": 4, "corners": 5,
    "form": "WDWLL", "key_players": "Messi (F) 5g, Busquets (M) 2a",
    "injuries": "Piqué (muscular)", "tactical_notes": "4-3-3, depende Messi",
    "h2h_vs_rival": "6W-2D-2L, 2.1 goals/partido", "forma_casa": "75%"
  }},
  "team_b_stats": {{
    "goals_avg": 1.2, "goals_for_last_5": [2,1,0,2,1], "goals_against_last_5": [1,0,2,1,1],
    "possession": 45, "xg": 1.3, "xga": 1.1, "shots_on_target": 3, "corners": 4,
    "form": "WWDWL", "key_players": "Benzema (F) 6g, Modric (M) 3a",
    "injuries": "Ninguna", "tactical_notes": "4-2-3-1",
    "h2h_vs_rival": "2W-2D-6L vs equipo_a", "forma_fuera": "45%"
  }},
  "parlays": {{
    "ultra_conservador": {{"picks": ["Local gana (70% + value)", "Under 2.5 (equilibrio)"], "odds": 1.75, "prob": 75, "ev": "+22%", "reason": "Capas 26-30: Valor + confianza + Kelly"}},
    "conservador": {{"picks": ["Local gana", "Over 1.5", "Gol en primer tiempo"], "odds": 3.5, "prob": 55, "ev": "+15%", "reason": "Capas 1-10 + psicología"}},
    "balanceado": {{"picks": ["Local gana", "Messi asist", "Benzema gol", "Over 2.5"], "odds": 6.3, "prob": 40, "ev": "+8%", "reason": "Capas 3-5 jugadores clave"}},
    "riesgoso": {{"picks": ["Local 2+ goles", "Messi gol", "Benzema gol", "Ambos anotan"], "odds": 20.0, "prob": 18, "ev": "+5%", "reason": "Capas 21-30 ineficiencias mercado"}}
  }},
  "modelos_matematicos": {{
    "poisson": {{"home_win": 68, "draw": 20, "away_win": 12, "goles_esperados_home": 1.8, "goles_esperados_away": 1.1}},
    "elo": {{"home_rating": 1750, "away_rating": 1600, "home_win_prob": 65, "elo_diff": 150}},
    "monte_carlo": {{"simulaciones": 50000, "home_win": 70, "draw": 18, "away_win": 12, "over_2_5": 62, "top_score": "2-1"}}
  }}
}}

CRÍTICO:
- CADA parlays viene de análisis específico de capas
- NO son independientes - están correlacionados por capas 21-30
- EV (Expected Value) DEBE ser positivo
- Kelly Criterion es stake management (capa 29)
"""


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
