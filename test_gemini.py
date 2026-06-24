#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from analyzer import _call_gemini

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
print(f"[TEST] GEMINI_API_KEY: {GEMINI_API_KEY[:20] if GEMINI_API_KEY else 'NO CONFIGURADA'}...")

if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY no está en el environment")
    sys.exit(1)

prompt = "Responde con un JSON valido. {'test': 'ok'}"

try:
    print("[TEST] Llamando a Gemini...")
    response = _call_gemini(prompt, max_tokens=200)
    print(f"[TEST] ✅ EXITO:\n{response[:500]}")
except Exception as e:
    print(f"[TEST] ❌ ERROR: {str(e)}")
    sys.exit(1)
