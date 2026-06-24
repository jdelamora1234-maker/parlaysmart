"""
ANALYZER v2.3 - OPTIMIZADO FULL STACK
Integra: Smart Cache + Kelly Criterion + Value Detection
Objetivo: Hit rate 60% → 70%+ con máximo ROI
"""

import json
from datetime import datetime
from smart_cache import cache
from kelly_optimizer import kelly
from value_detector import value
from analyzer_improved import analyze_match_improved

def analyze_match_optimized(team_a: str, team_b: str, sport: str,
                            competition: str, date_str: str,
                            use_cache: bool = True) -> dict:
    """
    ANALYZER v2.3 - Full optimization pipeline

    Pasos:
    1. Buscar en cache (si existe y valida)
    2. Si no: ejecutar analyzer v2.2
    3. Optimizar parlay allocation con Kelly
    4. Detectar value bets vs mercado
    5. Guardar en cache y tracking
    """

    print(f"\n{'='*80}")
    print(f"🚀 ANALYZER v2.3 - Full Optimization")
    print(f"{'='*80}\n")

    match_id = f"{team_a.replace(' ', '')}-{team_b.replace(' ', '')}-{date_str}"

    # PASO 1: Buscar en cache
    print(f"[v2.3] 📦 Paso 1: Verificar cache...")

    cached_analysis = None
    if use_cache:
        cached_analysis = cache.get(f"analysis:{match_id}")

        if cached_analysis:
            print(f"[v2.3] ✅ Análisis encontrado en cache (reutilizando)\n")
            analysis = cached_analysis
        else:
            print(f"[v2.3] ❌ Cache miss, ejecutar análisis\n")
            analysis = None
    else:
        analysis = None

    # PASO 2: Ejecutar analyzer si no hay cache
    if analysis is None:
        print(f"[v2.3] 🧠 Paso 2: Ejecutar analyzer v2.2...")

        analysis = analyze_match_improved(team_a, team_b, sport, competition, date_str)

        print(f"[v2.3] ✅ Análisis completado\n")

        # Guardar en cache
        cache.set(f"analysis:{match_id}", analysis, ttl_hours=48)

    # PASO 3: Optimizar allocation con Kelly Criterion
    print(f"[v2.3] 📊 Paso 3: Kelly Criterion optimization...")

    parlays_with_kelly = {}
    total_stake = 0

    for parlay_type, parlay_data in analysis.get("parlays", {}).items():
        prob = parlay_data.get("probabilidad_ganar", 0.5)
        odds = parlay_data.get("momios_combinados", 1.5)
        confidence = analysis.get("validations_passed", {}).get("layers_coverage", 0.5)

        kelly_info = kelly.calculate_kelly_with_confidence(prob, odds, confidence)

        parlay_data["kelly_fraction"] = kelly_info["kelly_fraction"]
        parlay_data["optimal_stake_pct"] = kelly_info["stake_fraction"]
        parlay_data["kelly_full"] = kelly_info["kelly_full"]

        # Calcular stake óptimo ($1000 bankroll)
        bankroll = 1000
        optimal_stake = bankroll * kelly_info["kelly_fraction"]
        parlay_data["optimal_stake"] = round(optimal_stake, 2)

        parlays_with_kelly[parlay_type] = parlay_data
        total_stake += kelly_info["kelly_fraction"]

    # Normalizar si suma > 100%
    if total_stake > 1.0:
        for parlay_type in parlays_with_kelly:
            parlays_with_kelly[parlay_type]["optimal_stake"] /= total_stake
            parlays_with_kelly[parlay_type]["optimal_stake_pct"] /= total_stake

    print(f"[v2.3] ✅ Kelly allocation optimized\n")

    # PASO 4: Detectar value bets
    print(f"[v2.3] 💎 Paso 4: Value bet detection...")

    predictions = {
        parlay_type: (data.get("probabilidad_ganar", 0.5),
                      data.get("momios_combinados", 1.5))
        for parlay_type, data in parlays_with_kelly.items()
    }

    value_bets = value.find_best_value_bets(predictions, threshold=0.05)

    # Agregar información de value bets a parlays
    for vb in value_bets:
        parlay_type = vb["parlay_name"]
        if parlay_type in parlays_with_kelly:
            parlays_with_kelly[parlay_type]["value_detected"] = True
            parlays_with_kelly[parlay_type]["value_pct"] = vb["value_pct"]
            parlays_with_kelly[parlay_type]["confidence_edge"] = vb["confidence"]

    print(f"[v2.3] ✅ Value bets detected: {len(value_bets)}\n")

    # PASO 5: Compilar resultado final
    print(f"[v2.3] 📋 Paso 5: Compilar resultado final...\n")

    final_analysis = {
        **analysis,
        "version": "2.3_optimized",
        "parlays_optimized": parlays_with_kelly,
        "value_bets_found": len(value_bets),
        "cache_status": "HIT" if cached_analysis else "MISS",
        "optimization_applied": {
            "kelly_criterion": True,
            "value_detection": True,
            "smart_cache": True,
        },
        "timestamp_analyzed": datetime.now().isoformat(),
    }

    # Guardar en cache
    cache.set(f"optimized:{match_id}", final_analysis, ttl_hours=24)

    return final_analysis


def print_analysis_summary(analysis: dict):
    """Imprime resumen bonito del análisis"""

    print(f"\n{'='*80}")
    print(f"📊 ANÁLISIS FINAL v2.3")
    print(f"{'='*80}\n")

    print(f"Versión: {analysis.get('version')}")
    print(f"Cache: {analysis.get('cache_status')}")
    print(f"Value bets encontrados: {analysis.get('value_bets_found')}\n")

    print(f"🎯 RECOMENDACIONES POR PARLAY:\n")

    for parlay_type, data in analysis.get("parlays_optimized", {}).items():
        print(f"{parlay_type.upper()}:")
        print(f"  Probabilidad: {data.get('probabilidad_ganar', 0)*100:.1f}%")
        print(f"  Odds: {data.get('momios_combinados', 0):.2f}")
        print(f"  Kelly optimal stake: ${data.get('optimal_stake', 0):.2f}")
        print(f"  Kelly %%: {data.get('optimal_stake_pct', 0)*100:.1f}%")

        if data.get("value_detected"):
            print(f"  💎 VALUE BET: +{data.get('value_pct', 0):.1f}%")

        print()


if __name__ == "__main__":
    print("[TEST] Analyzer v2.3\n")

    # Test
    result = analyze_match_optimized("Barcelona", "Real Madrid", "Futbol", "La Liga", "2026-06-24")

    print_analysis_summary(result)

    # Cache stats
    stats = cache.get_stats()
    print(f"📊 Cache Statistics:")
    print(f"  Total keys: {stats['total_keys']}")
    print(f"  Total hits: {stats['total_hits']}")
    print(f"  Hit rate: {stats['hit_rate']:.1f}%")
