# ⚡ INSTRUCCIONES URGENTES PARA RENDER.COM

**Status:** ParlaySmart en Render necesita 1 variable de entorno para funcionar.

---

## 🔴 PROBLEMA ACTUAL

La página en https://parlaysmart.onrender.com/ no está funcionando porque **falta GEMINI_API_KEY** en las environment variables de Render.

---

## 🟢 SOLUCIÓN (5 MINUTOS)

### Paso 1: Obtener Gemini API Key

1. Abre: https://aistudio.google.com/app/apikey
2. Click **"Get API Key"**
3. Click **"Create API key"**
4. Copia la clave (algo como: `AIzaSyD...`)

**ES GRATIS. Límite: 1,500 análisis/día**

---

### Paso 2: Agregar a Render Dashboard

1. Ir a: https://dashboard.render.com
2. Seleccionar el Web Service `parlaysmart`
3. Ir a **Settings**
4. Buscar **Environment Variables**
5. Agregar estas 3 variables:

```
GEMINI_API_KEY = AIzaSyDxxxxxxxxxxxx
SECRET_KEY = parlaysmart-secret-2025
ACCESS_CODE = Jorge2252
```

6. Click **Save**

---

### Paso 3: Redeploy

En Render Dashboard:
1. Click en **Deployments**
2. Click en el deployment más reciente
3. Click en **Redeploy**
4. Esperar 2-3 minutos

---

## ✅ Verificar Funcionamiento

Abre: https://parlaysmart.onrender.com/

Deberías ver:
- Pantalla de login (código: `Jorge2252`)
- Campo para buscar partido
- Botón "ANALIZAR PARLAY"

---

## 🎯 PRÓXIMOS PASOS

Una vez configurado GEMINI_API_KEY en Render:

1. Login con: `Jorge2252`
2. Buscar: "Barcelona vs Real Madrid"
3. Click: "ANALIZAR PARLAY"
4. Esperar 30 segundos
5. Ver análisis con 4 parlays

---

## ❓ Si Algo Falla

### Error: "GEMINI_API_KEY no encontrada"
- Verificar que la variable esté en Render Settings
- Hacer Redeploy después de agregar

### Error: "Timeout"
- Esperar 2 minutos (Gemini puede estar lento)
- Intentar de nuevo

### Error: "Invalid API Key"
- Verificar que la clave sea correcta
- Obtener nueva clave en https://aistudio.google.com/app/apikey

---

## 📊 Costo

```
Render:      GRATIS (free tier)
Gemini API:  GRATIS (1,500 análisis/día)
TOTAL:       $0/mes
```

---

**Eso es todo lo que necesitas hacer. Después de esto la página funcionará perfectamente.**
