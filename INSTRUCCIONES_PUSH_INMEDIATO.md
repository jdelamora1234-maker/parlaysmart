# ⚡ INSTRUCCIONES PARA HACER PUSH AHORA (5 MINUTOS)

## 🎯 LO QUE HICIMOS
Arreglamos dos problemas críticos en `analyzer.py`:

1. ✅ **max_tokens aumentado a 16000** (antes limitado a 8000)
2. ✅ **timeout aumentado a 90s** (antes 60s)
3. ✅ Commit listo: `24edd27`

---

## 📋 OPCIÓN A: Hacer Push desde tu máquina (RECOMENDADO)

### Paso 1: Copiar el archivo arreglado
```bash
# En tu terminal, en la carpeta de ParlaySmart
cp /tmp/parlaysmart/analyzer.py ./analyzer.py
```

### Paso 2: Ver los cambios
```bash
git diff analyzer.py
```

Deberías ver:
```diff
- "maxOutputTokens": min(max_tokens, 8000),
+ "maxOutputTokens": max_tokens,

- resp = requests.post(url, json=payload, timeout=60)
+ resp = requests.post(url, json=payload, timeout=90)

- raw_text = _call_gemini(prompt, max_tokens=12000
+ raw_text = _call_gemini(prompt, max_tokens=16000)
```

### Paso 3: Hacer commit
```bash
git add analyzer.py

git commit -m "🔧 Aumentar max_tokens a 16000 y timeout a 90s para análisis completo

- Remover límite min(max_tokens, 8000) que truncaba respuestas
- Aumentar max_tokens a 16000 para capturar análisis de 30 capas completo
- Aumentar timeout de 60s a 90s para manejar respuestas más grandes
- Gemini 2.0-flash ahora puede devolver análisis completo + stats + modelos

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

### Paso 4: Hacer push
```bash
git push origin main
```

**✅ LISTO**: Render auto-redeploy en 2-3 minutos

---

## 📋 OPCIÓN B: Push con GitHub CLI (Si lo tienes instalado)

```bash
# Copiar archivo
cp /tmp/parlaysmart/analyzer.py ./analyzer.py

# Commit con GitHub CLI
git add analyzer.py
git commit -m "..."
gh auth refresh -s repo
git push origin main
```

---

## 📋 OPCIÓN C: Hacer Push desde terminal con PAT

Si tienes tu Personal Access Token de GitHub:

```bash
# Reemplaza TOKEN con tu PAT real
cd /path/to/parlaysmart
git remote set-url origin https://USERNAME:TOKEN@github.com/jdelamora1234-maker/parlaysmart.git
git push origin main

# Luego, para mayor seguridad:
git remote set-url origin https://github.com/jdelamora1234-maker/parlaysmart.git
```

---

## ⏱️ TIMELINE ESPERADO

1. **T+0 min**: Haces push a GitHub
2. **T+30 seg**: Render detecta cambios
3. **T+1 min**: Render inicia build
4. **T+2-3 min**: Deploy completado
5. **T+3 min**: ParlaySmart actualizado en https://parlaysmart.onrender.com

---

## 🧪 TEST POST-DEPLOY

Una vez hecho el deploy:

### Test 1: Acceso básico
```
Ir a: https://parlaysmart.onrender.com
Ingresar código de acceso
```

### Test 2: Búsqueda simple
```
Equipo 1: Barcelona
Equipo 2: Real Madrid
Deporte: futbol
Competencia: La Liga
Fecha: hoy
```

### Test 3: Verificar respuesta completa
```
✅ Debería incluir:
   - 30 capas de análisis
   - Estadísticas de jugadores
   - Modelos matemáticos
   - 4 parlays (ultra, conservador, balanceado, riesgoso)
   - Probabilidades
```

### Test 4: Monitorear logs
```
En Render Dashboard:
- Logs → Ver que dice "✅ gemini-2.0-flash SUCCESS"
- Logs → Buscar "max_tokens": 16000
- Logs → NO debe haber "Read timed out"
```

---

## 🚨 SI ALGO FALLA

### Error: "Read timed out"
```
→ Significa que 90 segundos no fue suficiente
→ Aumentar a 120 segundos en analyzer.py línea 101
→ Hacer push de nuevo
```

### Error: "JSON parse error"
```
→ Significa que _extract_json no pudo parsear
→ Incrementar max_tokens (20000) para ver si ayuda
→ O cambiar a modelo "gemini-2.5-pro"
```

### Error: "Model overload 503"
```
→ Gemini está sobrecargado
→ Esperar 30 segundos e intentar de nuevo
→ El fallback a 2.5-flash debería manejar esto automáticamente
```

---

## ✅ CHEQUEA RÁPIDO

```bash
# Ver el archivo listo
cd /tmp/parlaysmart
cat analyzer.py | grep -A3 "maxOutputTokens"
cat analyzer.py | grep -A1 "timeout=90"
cat analyzer.py | grep -A1 "max_tokens=16000"
```

Deberías ver:
```
"maxOutputTokens": max_tokens,     ← SIN min()
timeout=90                          ← NO 60
max_tokens=16000                    ← NO 12000
```

---

## 📞 SI NECESITAS AYUDA

1. Comparte el output de:
   ```bash
   git log -1
   git status
   git remote -v
   ```

2. O los logs de Render:
   ```
   Render Dashboard → Logs
   Copia los últimos 20 líneas
   ```

---

**Genera**: Claude Code
**Fecha**: 2026-06-29
**Status**: Listo para deploy
