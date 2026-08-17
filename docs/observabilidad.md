# Observabilidad y análisis — proVida

## Qué se registra, y por qué el motor no calcula nada

`Mundo` acepta un `RegistroEventos` opcional (`provida/metrics/registro.py`). Si no se pasa ninguno, el mundo funciona exactamente igual que antes de la Fase 6 — observar es un extra, no un requisito. Cuando hay un registro conectado, se acumulan dos tipos de datos crudos:

- **Nacimientos** (uno por cada `h-divide` exitoso): turno, id del organismo, id del padre, generación, merit y qué tareas ya tenía resueltas al nacer.
- **Snapshots** (fotos de la población en un turno dado, tomadas explícitamente por quien analiza, no automáticamente por el motor): población total, merit promedio, y conteo de organismos por tarea resuelta.

El registro no calcula promedios, porcentajes ni gráficas — solo acumula. Eso se decidió a propósito: así `provida/world/grid.py` no necesita saber nada de `pandas` ni de `matplotlib`, y cualquier forma nueva de analizar los datos (un notebook, un dashboard) se puede construir después sin tocar el motor de simulación.

## "Generación" como profundidad de linaje

Como quedó anotado en el glosario (Fase 1), este proyecto no tiene generaciones sincronizadas globalmente — la reproducción es asíncrona y solapada. Cada organismo guarda `generacion = generacion_del_padre + 1`, es decir, cuántos ancestros lo separan del fundador que colocamos manualmente al principio.

**Hallazgo real al construir esta fase, no anticipado de antemano:** en una corrida de 60 000 turnos con 1157 nacimientos totales, la generación máxima observada fue **14** — no cientos, como uno podría esperar ingenuamente. La razón: en nuestro diseño, un organismo que se reproduce exitosamente **no muere ni deja de existir** — "renace" con el mismo genoma y sigue intentando reproducirse indefinidamente (ver sub-fase 4). Eso significa que un mismo padre longevo puede acumular decenas de hijos, todos en la misma generación (`padre.generacion + 1`), en vez de que el linaje se "estire" en una cadena larga de padre→hijo→nieto. La mayoría de los nacimientos terminan concentrados en las generaciones 4 a 9, no distribuidos uniformemente. Esto no es un error: es una consecuencia directa y honesta de que este MVP no modela envejecimiento ni un límite al número de veces que un organismo puede reproducirse — solo compite por espacio cuando otro organismo nace en su celda.

## Las tres gráficas de `examples/demo_laboratorio.py`

1. **Merit promedio y % con tarea resuelta, por turno** — la vista más directa de "la evolución ocurriendo en tiempo real". En la corrida de referencia, ambas curvas suben juntas de forma casi idéntica en los primeros ~5000 turnos y luego se estabilizan cerca del máximo.
2. **Fitness promedio por generación** — usa la definición de generación de arriba. Sube de golpe entre la generación 0 y la 2, y se mantiene estable después, porque para ese punto casi toda la población desciende ya del linaje que resuelve NAND.
3. **Árbol filogenético simplificado** — de los primeros 40 nacimientos únicamente (una rejilla saturada de cientos de organismos sería ilegible). Coloreado por si el organismo ya tenía NAND resuelto al nacer. Se ve con claridad cómo, ya desde la segunda generación, prácticamente todos los descendientes visibles vienen del linaje con tarea — los fundadores "control" casi no llegan a reproducirse dentro de esa ventana.

## Cómo correr el laboratorio

```bash
pip install -e ".[analisis]"
python3 examples/demo_laboratorio.py
```

Las gráficas se guardan en `runs/` (no se versiona — ver `.gitignore` — porque son salidas generadas, no código fuente).
