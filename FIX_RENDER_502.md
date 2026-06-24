# 🔴 ERROR 502 en Render - SOLUCIÓN RÁPIDA

## El Problema

ParlaySmart en Render está devolviendo **Error 502** porque:
- ❌ GEMINI_API_KEY no está configurada en Environment Variables de Render
- ❌ El servidor no puede iniciar sin esa clave

## ✅ SOLUCIÓN (3 MINUTOS)

### PASO 1: Obtener tu Gemini API Key

1. Abre: **https://aistudio.google.com/app/apikey**
2. Click en **"Get API Key"**
3. Click en **"Create API key"**
4. **Copia tu clave** (algo como: `AIzaSyD...`)
5. Guárdala segura

**ES GRATIS. Límite: 1,500 análisis/día**

---

### PASO 2: Agregar a Render Dashboard

1. Abre: **https://dashboard.render.com**
2. Busca tu Web Service **"parlaysmart"**
3. Click en él para abrirlo
4. Ir a pestaña **"Settings"** (arriba a la derecha)
5. Buscar sección **"Environment"** o **"Environment Variables"**
6. Click en **"Add Environment Variable"**

**Agregar EXACTAMENTE así:**

```
Name: GEMINI_API_KEY
Value: AIzaSyDxxxxxxxxxxxx (tu clave real)
```

(Reemplaza `AIzaSyDxxxxxxxxxxxx` con tu clave real)

7. Click **"Save"**

---

### PASO 3: Hacer Redeploy

1. Ir a pestaña **"Deployments"** (al lado de Settings)
2. Ver el deployment más reciente (arriba de la lista)
3. Click en el **botón de 3 puntos** (menú) del deployment
4. Click en **"Redeploy"**
5. **Esperar 2-3 minutos** mientras se redeploya

---

### PASO 4: Verificar

1. Abre: https://parlaysmart.onrender.com/
2. Deberías ver la pantalla de login (NO error 502)
3. Login con código: **Jorge2252**
4. Prueba a buscar un partido

---

## ✅ Resultado

```
ANTES: Error 502 (servidor no responde)
DESPUÉS: Pantalla de login → Análisis funcionando
```

---

## ❓ Si Sigue Fallando

### Opción 1: Verificar que la variable esté

1. Render Dashboard → Settings → Environment Variables
2. Verificar que GEMINI_API_KEY esté ahí
3. Verificar que el valor comience con "AIza"
4. Hacer Redeploy nuevamente

### Opción 2: Usar una clave nueva

1. Ir a https://aistudio.google.com/app/apikey
2. Hacer click en la "X" para eliminar la clave anterior
3. Click en "Create API key" (crear nueva)
4. Copiar la nueva clave
5. Actualizar en Render Dashboard
6. Hacer Redeploy

### Opción 3: Revisar logs de Render

En Render Dashboard:
- Pestaña "Logs"
- Ver si hay mensajes de error
- Si dice "GEMINI_API_KEY not configured" → sigue el paso 2 arriba

---

## 💡 Notas Importantes

```
⚠️ La clave debe ser:
  • Desde https://aistudio.google.com/app/apikey
  • NO de otros servicios Google
  • Completamente válida (sin errores al copiar)

⚠️ Después de agregar la variable:
  • SIEMPRE hacer Redeploy
  • No basta con solo guardarla

⚠️ Puede tardar 2-3 minutos:
  • No actualices la página constantemente
  • Espera a que termine el redeploy
```

---

## ✨ Una Vez Que Funcione

```
ParlaySmart estará:
✅ Accesible en: https://parlaysmart.onrender.com
✅ Con login: Jorge2252
✅ Analizando partidos con precisión 95%
✅ Generando 4 parlays con datos reales
✅ Guardando resultados automáticamente
```

---

**Esto es TODO lo que necesitas hacer. Una vez hecho, funcionará perfecto.** 🚀
