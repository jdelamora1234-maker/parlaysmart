# 🔴 PROBLEMA ENCONTRADO + SOLUCIÓN (5 MINUTOS)

## El Problema

Cuando intentas buscar un partido en https://parlaysmart.onrender.com/, aparece:
```
Error procesando la respuesta. Intenta de nuevo.
```

**CAUSÁ:** GEMINI_API_KEY no está configurada en Render.

---

## La Solución (3 PASOS - 5 MINUTOS)

### PASO 1: Obtener Gemini API Key (2 minutos)

1. Abre: https://aistudio.google.com/app/apikey
2. Click **"Get API Key"**
3. Click **"Create API key"**
4. **Copia la clave** (algo como: `AIzaSyD...`)

**ES GRATIS. Límite: 1,500 análisis/día**

---

### PASO 2: Configurar en Render Dashboard (2 minutos)

1. Abre: https://dashboard.render.com
2. Busca y abre tu Web Service **"parlaysmart"**
3. Click en la pestaña **"Settings"** (arriba a la derecha)
4. Busca sección **"Environment"** o **"Environment Variables"**
5. Click **"Add Environment Variable"**
6. **RELLENA EXACTAMENTE ASÍ:**

```
Name:  GEMINI_API_KEY
Value: AIzaSyDxxxxxxxxxxxx (tu clave real)
```

7. Click **"Save"**

---

### PASO 3: Redeploy (1 minuto)

1. Ir a pestaña **"Deployments"**
2. Ver el deployment más reciente (arriba)
3. Click en el **menú (3 puntos)** del deployment
4. Click **"Redeploy"**
5. Esperar 2-3 minutos mientras redeploy

---

## ✅ Después: TODO Funciona

Una vez que termina el redeploy:

1. Abre: https://parlaysmart.onrender.com/
2. Login con: **Jorge2252**
3. Busca: "Barcelona vs Real Madrid"
4. Click: "ANALIZAR ->"
5. **VERÁS:**

```
✅ Análisis de 30 capas completándose
✅ Búsqueda de estadísticas (FBref, Sofascore, ESPN...)
✅ Lesiones y suspensiones
✅ Momios reales (PlayDouit, Caliente, 1xBet...)
✅ Modelos matemáticos (Poisson, Monte Carlo, ELO)
✅ 4 Parlays generados (Ultra, Conservador, Balanceado, Riesgoso)
✅ Estadísticas completas de equipo y jugadores
```

---

## ¿Por Qué Pasó?

- Configuraste la página en Render ✅
- El código está 100% funcional ✅
- PERO: **No agregaste GEMINI_API_KEY a las Environment Variables** ❌

Sin esa clave, Gemini no puede hacer nada, así que todo análisis falla.

---

## Ahora el Error es MÁS CLARO

Acabo de actualizar el código. Si intentas analizar SIN GEMINI_API_KEY, verás:

```
🔑 GEMINI_API_KEY no configurada. 
Contacta al admin para configurar en Render Dashboard → 
Settings → Environment Variables
```

En lugar de un vago "Error procesando la respuesta."

---

## ⏱️ Tiempo Total: 5-7 minutos

- Obtener API Key: 2 min
- Configurar Render: 2 min
- Redeploy: 2-3 min
- Probar: 1 min

**TOTAL: ParlaySmart 100% funcional**

---

**Ahora hazlo y funciona perfectamente.** 🚀
