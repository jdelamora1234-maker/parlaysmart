# 🚀 ParlaySmart en Render.com - Guía Completa

## Paso 1: Obtener API Keys (5 minutos)

### 🔑 GEMINI API KEY (GRATIS - Recomendado)

1. Ir a: https://aistudio.google.com/app/apikey
2. Click en "Get API Key"
3. Click en "Create API key"
4. Copiar la clave (algo como: `AIzaSyD...`)
5. **Guardar en seguro** (lo necesitarás en el paso 3)

**Límite:** 1,500 análisis gratis por día (suficiente para ~50 usuarios)

---

## Paso 2: Preparar Código para Render (2 minutos)

### ✅ Verificar `requirements.txt`

```bash
cd /tmp/parlaysmart
cat requirements.txt
```

Debe contener:
```
flask>=3.0.0
flask-cors>=4.0.0
flask-limiter>=3.0.0
google-genai>=1.0.0
gunicorn>=21.0.0
requests>=2.31.0
```

Si faltan librerías, ejecuta:
```bash
pip install -r requirements.txt
```

### ✅ Verificar `Procfile`

Debe contener exactamente:
```
web: gunicorn server:app
```

Si no existe o está diferente:
```bash
echo "web: gunicorn server:app" > Procfile
```

---

## Paso 3: Desplegar en Render.com (10 minutos)

### Opción A: Via GitHub (Recomendado - Automático)

1. **Push a GitHub**
   ```bash
   cd /tmp/parlaysmart
   git init
   git add .
   git commit -m "ParlaySmart v2.1 - Ready for production"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/parlaysmart.git
   git push -u origin main
   ```

2. **Crear cuenta en Render.com**
   - Ir a: https://render.com
   - Registrarse con GitHub (más fácil)

3. **Crear nuevo "Web Service"**
   - Click en "New +" → "Web Service"
   - Seleccionar el repositorio `parlaysmart`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn server:app`
   - **Plan:** Free (o Starter si quieres mayor uptime)

4. **Agregar Environment Variables**
   - En Settings → Environment Variables, agregar:
     ```
     GEMINI_API_KEY=tu_clave_de_gemini
     ODDS_API_KEY=opcional
     OPENWEATHER_API_KEY=opcional
     SECRET_KEY=parlaysmart-secret-2025
     ACCESS_CODE=Jorge2252
     ```

5. **Deploy**
   - Click en "Deploy"
   - Esperar 3-5 minutos

6. **Obtener URL**
   ```
   https://parlaysmart-XXXXX.onrender.com
   ```

---

### Opción B: Render + GitHub Manual

Si prefieres pull automático sin GitHub personal:

1. Copiar código a Render directamente:
   - Click en "New Web Service"
   - Seleccionar "Public Git repository"
   - Pegar: `https://github.com/jdelamora1234-maker/parlaysmart.git`
   - Hacer merge de tus cambios primero

---

## Paso 4: Probar Localmente PRIMERO (Recomendado)

### ✅ Correr en local antes de enviar a Render

```bash
cd /tmp/parlaysmart

# 1. Crear .env
echo "GEMINI_API_KEY=tu_clave_gemini" > .env
echo "SECRET_KEY=parlaysmart-secret-2025" >> .env
echo "ACCESS_CODE=Jorge2252" >> .env

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar servidor
python3 server.py
```

### ✅ Probar en navegador

1. Ir a: http://localhost:5050
2. Se mostrará pantalla de login
3. Ingresar código: `Jorge2252`
4. Buscar un partido (ej: "Barcelona vs Real Madrid")
5. Esperar análisis con 30 capas

---

## Paso 5: Verificar Funcionamiento

### ✅ Checklist post-deploy

- [ ] URL en Render.com es accesible
- [ ] Pantalla de login aparece
- [ ] Código `Jorge2252` permite entrar
- [ ] Búsqueda de partido funciona
- [ ] Análisis genera parlays (toma 20-30 segundos)
- [ ] 4 tipos de parlays aparecen (ultra, conservador, balanceado, riesgoso)

### ❌ Si algo no funciona

**Error: "GEMINI_API_KEY no encontrada"**
- Verificar que .env esté creado
- Verificar que GEMINI_API_KEY esté en Environment Variables de Render
- Restart la app en Render

**Error: "No se pudo obtener datos"**
- Gemini API puede estar sobrecargada (reintentar)
- Verificar que la clave de Gemini sea válida
- Probar con una búsqueda más simple (ej: "Barcelona Madrid")

**Error: Timeout (toma >60 segundos)**
- En Render Free el servidor es lento
- Upgrade a Starter ($7/mes) para mejor velocidad
- O agregar manualmente cached data

---

## Costo Final

| Servicio | Costo | Notas |
|----------|-------|-------|
| **Render.com** | Gratis | Free tier (ejecuta gratis pero lento) |
| **Gemini API** | Gratis | Hasta 1,500 análisis/día |
| **Dominio personalizado** | Opcional | Si quieres parlaysmart.com (~$10/año) |
| **TOTAL** | **$0** | (o $7 en Render Starter) |

---

## URLs Importantes

| Recurso | URL |
|---------|-----|
| **Gemini API Key** | https://aistudio.google.com/app/apikey |
| **Render.com** | https://render.com |
| **GitHub** | https://github.com |
| **Tu ParlaySmart** | https://parlaysmart-XXXXX.onrender.com |

---

## Troubleshooting

### "El servidor tarda mucho"
```bash
# Agregar caching de parlays (en app.py futuro)
# O upgrade a Render Starter ($7/mes)
```

### "Gemini no responde"
```bash
# Cambiar modelo en analyzer.py línea 78:
models_to_try = ["gemini-2.0-flash", "gemini-1.5-pro"]
```

### "Necesito cambiar código en Render"
```bash
# 1. Cambiar localmente
# 2. Git push a GitHub
# 3. Render redeploy automático
```

---

## Próximos Pasos Después del Deploy

1. **Dashboard de stats** (Fase C)
   - Visualizar hit rate en vivo
   - Ver análisis históricos
   - Gráficos de rentabilidad

2. **Agregar más usuarios**
   - Cambiar ACCESS_CODE por PIN codes únicos
   - Ver tracking de cada usuario
   - Validar hit rates por usuario

3. **Escalamiento**
   - Si > 1,500 análisis/día → Gemini cobra $0.075/millón tokens
   - Si necesitas mejor uptime → Render Starter ($7/mes)
   - Si quieres DB real → PostgreSQL gratis en Render

---

**Preguntas?** Revisa los archivos de documentación:
- `STATUS_ACTUAL.md` — Estado completo del proyecto
- `MEJORAS_IMPLEMENTADAS_v2.1.md` — Qué se mejoró
- `ROADMAP_B_TO_C.md` — Plan de escalamiento
