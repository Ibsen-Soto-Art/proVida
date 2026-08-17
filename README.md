# proVida

Simulador de vida digital inspirado en [Avida](https://en.wikipedia.org/wiki/Avida) (Ofria, Adami, Pennock — Michigan State University), construido desde cero como proyecto de aprendizaje.

Organismos digitales — programas autorreplicantes que corren sobre una máquina virtual propia — compiten por espacio y tiempo de CPU en un mundo simulado. Mutan al copiarse, y los que resuelven tareas lógicas obtienen más ciclos de ejecución, lo que se traduce en más descendencia. La selección natural y la evolución de complejidad emergen de estas reglas simples, sin que el sistema optimice nada de forma explícita.

## Estado del proyecto

En desarrollo activo. Ver [docs/](docs/) para la documentación completa de diseño.

## Documentación

- [Visión técnica](docs/vision-tecnica.md) — problema, objetivo de aprendizaje, alcance del MVP.
- [Glosario](docs/glosario.md) — términos técnicos con su analogía biológica.
- [Arquitectura](docs/arquitectura.md) — diseño de la VM, el lenguaje de instrucciones, el motor de mundo/población, mutación y tareas lógicas.
- [Testing](docs/testing.md) — estrategia de pruebas: determinista, estadística, emergente y de regresión.
- [Observabilidad](docs/observabilidad.md) — qué métricas se registran, "generación" como profundidad de linaje, y las gráficas del laboratorio.

## Stack

Python 3.11+.

## Desarrollo

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q --cov=provida --cov-report=term-missing
```

## Demos

Cada sub-fase de desarrollo tiene un script ejecutable en [examples/](examples/) que demuestra el mecanismo correspondiente:

```bash
python3 examples/demo_genoma_fijo.py         # VM ejecutando un genoma fijo
python3 examples/demo_autorreplicacion.py    # un organismo se copia a sí mismo
python3 examples/demo_mutacion.py            # mutación durante la copia
python3 examples/demo_poblacion.py           # una rejilla se llena de organismos
python3 examples/demo_tareas.py              # tareas lógicas como fuente de merit
python3 examples/demo_seleccion_natural.py   # selección natural emergente, verificada
python3 examples/demo_laboratorio.py         # gráficas: fitness, generación y árbol filogenético
```

El último requiere las dependencias de análisis: `pip install -e ".[analisis]"`.

## Licencia

Proyecto personal de aprendizaje / portafolio.
