# Estrategia de testing — proVida

## Por qué esto no es testing de CRUD

En una aplicación típica (crear/leer/actualizar/borrar registros), casi todo el comportamiento es determinista: mismo input, mismo output, siempre. proVida no es así por diseño — la mutación y el planificador de la población son intencionalmente probabilísticos. Probar este tipo de sistema requiere combinar tres técnicas distintas, cada una para un tipo de comportamiento distinto:

| Tipo de comportamiento | Técnica de prueba | Ejemplo en este proyecto |
|---|---|---|
| Determinista (`tasa_mutacion=0`, sin ambiente) | Assert directo sobre un valor exacto — igual que un CRUD | `tests/test_vm_basico.py`, `tests/test_autorreplicacion.py` |
| Probabilístico con tasa conocida | Muchas repeticiones con semilla fija, verificar que la tasa empírica cae dentro de una tolerancia | `tests/test_mutacion.py` (tasa de mutación), `tests/test_mundo.py` (scheduling ponderado) |
| Emergente (¿la selección ocurre de verdad?) | Correr el sistema completo y comparar contra un control nulo | `tests/test_seleccion_natural.py` |

Además de estas tres, hay una cuarta categoría que no encaja en ninguna de las anteriores:

| Tipo de prueba | Para qué sirve | Dónde |
|---|---|---|
| Regresión sobre organismos ancestrales | Congelar números EXACTOS de corridas conocidas, para detectar cambios silenciosos en un refactor futuro, aunque el cambio no rompa ninguna prueba de las categorías anteriores | `tests/test_regresion_organismos_ancestrales.py` |

## Por qué la semilla (`random.Random(N)`) es parte del contrato de la prueba

Todas las fuentes de aleatoriedad de la CPU (mutación, scheduling, inputs del ambiente) pasan por un único `random.Random` inyectado explícitamente — nunca se usa el generador global de Python. Esto tiene dos razones:

1. **Reproducibilidad:** una corrida con la misma semilla produce exactamente la misma secuencia de eventos, siempre. Sin esto, las pruebas de regresión serían imposibles de escribir.
2. **Aislamiento:** dos organismos (o dos pruebas) que usan generadores distintos no interfieren entre sí, incluso si corren en el mismo proceso.

## Cobertura

El proyecto usa `pytest-cov` (`pytest --cov=provida --cov-report=term-missing`). Al cerrar la Fase 5, la cobertura de `provida/` es del 100% sobre líneas ejecutables. Esto no significa "cero bugs" — significa que no hay ramas de código que nunca se ejecuten en ningún test, lo cual es el mínimo razonable antes de seguir construyendo encima.

## Qué NO se prueba (todavía) y por qué

- **Rendimiento / escalabilidad:** el MVP prioriza claridad conceptual (ver `docs/vision-tecnica.md`, sección "qué no incluye"). No hay pruebas de que el sistema soporte poblaciones de miles de organismos.
- **Corridas muy largas (millones de turnos):** las pruebas de regresión usan 100k turnos como techo práctico para que la suite completa siga corriendo en segundos, no minutos.
- **Propiedades formales verificadas exhaustivamente (property-based testing con `hypothesis`):** se consideró, pero para el tamaño actual del proyecto las pruebas estadísticas con semillas fijas ya cubren el mismo tipo de riesgo (comportamiento incorrecto solo bajo ciertos valores) sin añadir una dependencia nueva. Candidato razonable para la Fase 7 si el espacio de instrucciones crece.

## Cómo correr la suite

```bash
pytest -q                                    # rápido, sin cobertura
pytest -q --cov=provida --cov-report=term-missing   # con reporte de cobertura
```
