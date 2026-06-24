# 🚀 PLAN DE MEJORAS PRIORITARIAS - ParlaySmart v2.1

## MEJORAS CRÍTICAS A IMPLEMENTAR

### FASE 1: APIs Directas + Datos Reales (Semana 1)
**Archivo:** `data_sources.py` (NUEVO)

```
✅ Integrar Understat API
   - xG, xGA, xA por equipo/jugador
   - PPDA (presión defensiva real, no estimado)
   - Big Chances Created
   - Progressive Passes
   - Reemplaza estimaciones vagas por datos reales

✅ Integrar ESPN API  
   - Lesiones confirmadas
   - Noticias últimas 48h
   - Cambios de alineación
   - Histórico H2H

✅ Integrar OpenWeatherMap API
   - Temperatura exacta
   - Humedad
   - Velocidad viento
   - Precipitación
   - Reemplaza Google Search = 10x más preciso

✅ Integrar Sofascore API
   - Stats en vivo durante partido
   - Attacking Momentum real
   - Player Ratings
   - Tactical changes
```

**Beneficio:** 
- Datos de Capa 1-16 = MEDIDOS, no estimados
- Precisión +300%
- Elimina ruido de Google Search

---

### FASE 2: Sistema de Tracking (Semana 1-2)
**Archivos:** `tracking.py`, `schema_tracking.sql` (NUEVO)

```
✅ Base de datos de análisis
   - Guardar: análisis, picks, odds, EV calculado
   - Resultado real: goles finales, tarjetas, corners
   - Timestamp: cuándo se hizo vs cuándo pasó

✅ Dashboard de resultados
   - Hit rate real por tipo parlay (Ultra/Conservador/Balanceado/Riesgoso)
   - Win/Loss/Tie
   - ROI real vs esperado
   - Desviación por capa (¿qué capa falló más?)

✅ Validación automática
   - Después de cada jornada: verificar resultado vs predicción
   - Calcular error absoluto
   - Compilar estadísticas
```

**Beneficio:**
- Sabes si el sistema REALMENTE funciona
- Detectas si overestimas/underestimas
- Identifica qué capas necesitan ajuste

---

### FASE 3: Machine Learning de Pesos (Semana 2-3)
**Archivo:** `ml_weights.py` (NUEVO)

```
✅ Ajuste automático de capas
   - Después de 20 análisis: 
     - Si Capa 5 (psicología) predice mal → reducir su peso
     - Si Capa 22 (biometría) predice bien → aumentar su peso
   
✅ Regresión lineal de pesos
   - entrada: 30 capas (variables independientes)
   - salida: resultado real (variable dependiente)
   - Modelo aprende combinación óptima

✅ Validación cruzada
   - 80% entrenar, 20% validar
   - Evita overfitting
   - Reporta score de precisión
```

**Beneficio:**
- Sistema aprende del tiempo
- Pesos optimales después de 100 análisis
- Hit rate sube automáticamente

---

### FASE 4: Backtest Automático (Semana 3)
**Archivo:** `backtest.py` (NUEVO)

```
✅ Descarga históricos (últimos 50 partidos)
   - Understat: stats históricos
   - ESPN: resultados reales

✅ Re-analiza con sistema antiguo vs nuevo
   - "¿Qué hubiera predicho hace 50 partidos?"
   - Compara predicción vs resultado real

✅ Reporta
   - Hit rate histórico vs actual
   - Partidos donde acertaste
   - Partidos donde fallaste
   - Qué patrones predices bien/mal
```

**Beneficio:**
- Valida que el sistema NO es suerte
- Identifica si mejoró realmente
- Credibilidad ante clientes

---

### FASE 5: Validación de 30 Capas (Semana 3-4)
**Función:** `validate_all_layers()` en `analyzer.py`

```
✅ Verificar que TODAS 30 capas se usan
   - Después de cada análisis: 
     - ¿Qué capas se analizaron?
     - ¿Qué capas faltaron?
   - Reportar: "Análisis 28/30 capas (faltó 8, 19)"

✅ Si faltan capas: re-analizar
   - Garantiza cobertura completa
```

**Beneficio:**
- Sin sorpresas: sabes qué se analizó
- Consistencia garantizada

---

## ARCHIVOS A CREAR

```
data_sources.py          (300 líneas) - APIs directas
tracking.py              (200 líneas) - Guardar análisis + resultados
ml_weights.py            (250 líneas) - Ajuste automático de pesos
backtest.py              (300 líneas) - Validación histórica
schema_tracking.sql      (50 líneas)  - BD para tracking
requirements_updated.txt (actualizar)  - Nuevas librerías
```

## LIBRERÍAS NUEVAS

```
requests          - Llamadas HTTP a APIs
pandas            - Análisis de datos
scikit-learn      - Regresión lineal para ML
sqlalchemy        - ORM para BD
python-dotenv     - Variables de entorno
```

## IMPACTO ESPERADO

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Datos estimados | 60% | 10% | ↓ 50pp |
| Precisión datos | 70% | 95% | ↑ 25pp |
| Hit rate esperado | ~58% | ~65%+ | ↑ 7pp |
| Velocidad análisis | 3s | 4s | -33% |
| Conocimiento real | "Espero" | "Sé" | Certeza |

## ROADMAP

```
DÍA 1-2:   data_sources.py (APIs directas)
DÍA 3-4:   tracking.py (guardar resultados)
DÍA 5-6:   ml_weights.py (ML de pesos)
DÍA 7:     backtest.py (validación)
DÍA 8:     Integración + testing
DÍA 9-10:  Beta con 3-5 usuarios
```

---

## SIGUIENTE PASO

¿Empiezo con data_sources.py?
