#!/usr/bin/env python3
"""
Script de prueba para ParlaySmart sin necesidad de Render
Prueba: análisis de un partido y generación de parlays
"""

import os
import sys
import json

def main():
    print("\n" + "="*70)
    print("🎰 PARLAYSMART LOCAL TEST")
    print("="*70)

    # 1. Verificar .env
    print("\n1️⃣ Verificando configuración...")
    if not os.path.exists('.env'):
        print("❌ .env no encontrado")
        print("\n   Para obtener Gemini API Key:")
        print("   1. Ir a: https://aistudio.google.com/app/apikey")
        print("   2. Click en 'Get API Key' → 'Create API key'")
        print("   3. Crear archivo .env con:")
        print("      GEMINI_API_KEY=tu_clave_aqui")
        return

    # Leer .env
    env_vars = {}
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env_vars[k.strip()] = v.strip()

    gemini_key = env_vars.get('GEMINI_API_KEY', '').strip()
    if not gemini_key or gemini_key.startswith('tu_'):
        print("❌ GEMINI_API_KEY no está configurada en .env")
        print("   Actualiza .env con tu clave de https://aistudio.google.com/app/apikey")
        return

    print(f"✅ GEMINI_API_KEY configurada: {gemini_key[:20]}...")
    os.environ['GEMINI_API_KEY'] = gemini_key

    # 2. Importar analyzer
    print("\n2️⃣ Importando módulos...")
    try:
        from analyzer import analyze_match
        print("✅ Módulos importados correctamente")
    except Exception as e:
        print(f"❌ Error al importar: {e}")
        return

    # 3. Análisis de prueba
    print("\n3️⃣ Analizando partido de ejemplo...")
    print("   (Barcelona vs Real Madrid - Hoy)")
    print("   (Esto toma 30-60 segundos...)")

    try:
        result = analyze_match(
            team_a="Barcelona",
            team_b="Real Madrid",
            sport="Futbol",
            competition="La Liga",
            date_str="hoy",
            context="Clásico español, Camp Nou"
        )

        print("\n✅ ANÁLISIS COMPLETADO\n")

        # Mostrar resultado
        if isinstance(result, dict):
            print("📊 RESULTADO:")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:1000])
            print("\n... (resultado truncado)")

            # Resumen
            prediccion = result.get('prediccion', {})
            parlays = result.get('parlays', {})

            print("\n" + "="*70)
            print("📈 RESUMEN")
            print("="*70)
            print(f"Predicción: {prediccion.get('ganador', '?')}")
            print(f"Probabilidad local: {prediccion.get('prob_local', 0):.1%}")
            print(f"Probabilidad empate: {prediccion.get('prob_empate', 0):.1%}")
            print(f"Probabilidad visitante: {prediccion.get('prob_visitante', 0):.1%}")

            if parlays:
                print(f"\n🎯 Parlays generados: {len(parlays)} tipos")
                for parlay_type in ['ultra_conservador', 'conservador', 'balanceado', 'riesgoso']:
                    if parlay_type in parlays:
                        p = parlays[parlay_type]
                        print(f"   • {parlay_type}: {len(p.get('selecciones', []))} picks")

            print("\n✅ SISTEMA FUNCIONA CORRECTAMENTE")
            print("\nPróximos pasos:")
            print("1. Desplegar en Render.com: ver SETUP_RENDER.md")
            print("2. Compartir URL con clientes")
            print("3. Usar código de acceso: Jorge2252")

        else:
            print(f"⚠️ Resultado inesperado: {result}")

    except Exception as e:
        print(f"\n❌ Error en análisis: {e}")
        print("\nVerifica:")
        print("• GEMINI_API_KEY es válida (obtén de https://aistudio.google.com)")
        print("• Tienes conexión a internet")
        print("• Gemini API no está sobrecargada (reintentar más tarde)")
        print("• Los módulos importan correctamente (python3 -m pytest)")

if __name__ == "__main__":
    main()
