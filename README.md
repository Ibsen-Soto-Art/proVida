# proVida

Simulador de vida digital inspirado en [Avida](https://en.wikipedia.org/wiki/Avida) (Ofria, Adami, Pennock — Michigan State University), construido desde cero como proyecto de aprendizaje: no reimplementa Avida, reconstruye sus principios para entenderlos a fondo.

**[Ver el sitio en vivo →](https://proVida.ibsen-soto.pro)** — hallazgos y gráficas de un experimento real corrido con este código.

## Qué es

Organismos digitales — programas autorreplicantes que corren sobre una máquina virtual propia, escrita desde cero en Python — compiten por espacio y tiempo de CPU en un mundo simulado. Mutan al copiarse, y los que resuelven tareas lógicas obtienen más ciclos de ejecución, lo que se traduce en más descendencia. La selección natural y la evolución de complejidad emergen de estas reglas simples, sin que ningún código las declare explícitamente — se verifican con datos, no se asumen (ver el hallazgo destacado abajo).

## Hallazgo destacado

Dos genotipos de **exactamente la misma longitud** compiten por el mismo espacio finito: uno resuelve una tarea lógica (merit ×8), el otro no. Partiendo de un empate 50/50, el genotipo con tarea termina representando el **100% de una población de 225 organismos** en 100 000 turnos — sin que ninguna línea de código decida quién debe ganar. Un control nulo (mismo experimento, sin ambiente ni mutación) confirma que la dominancia no es un artefacto: la proporción se queda cerca de 50/50. Ver [`examples/demo_seleccion_natural.py`](examples/demo_seleccion_natural.py) y [`tests/test_seleccion_natural.py`](tests/test_seleccion_natural.py).

## Cómo está construido

| Pieza | Qué hace |
|---|---|
| [`provida/vm/`](provida/vm/) | Máquina virtual: registros de 32 bits, pila, punteros de instrucción, 21 opcodes (incluyendo saltos por direccionamiento de contenido tipo nop-label) |
| [`provida/mutation/`](provida/mutation/) | Sustitución, inserción y deleción durante la auto-copia |
| [`provida/world/`](provida/world/) | Rejilla 2D toroidal, planificador ponderado por merit, reemplazo por vecindario |
| [`provida/tasks/`](provida/tasks/) | Tareas lógicas (NOT/AND/NAND) como fuente de recompensa metabólica |
| [`provida/metrics/`](provida/metrics/) | Registro de eventos y linaje, para observar la evolución con datos |
| [`sitio/`](sitio/) | Genera el sitio estático de resultados a partir de una corrida real |

Cero dependencias externas para el núcleo (`provida/`) — solo la librería estándar de Python. `matplotlib`/`pandas`/`networkx` son opcionales, solo para análisis y visualización.

## Documentación

Todo el proceso de diseño está documentado en [`docs/`](docs/), fase por fase:

- [Visión técnica](docs/vision-tecnica.md) — problema, objetivo de aprendizaje, alcance del MVP.
- [Glosario](docs/glosario.md) — términos técnicos con su analogía biológica.
- [Arquitectura](docs/arquitectura.md) — diseño de la VM, el lenguaje de instrucciones, mutación, tareas lógicas, y la extensión de direccionamiento por contenido.
- [Testing](docs/testing.md) — estrategia de pruebas: determinista, estadística, emergente y de regresión.
- [Observabilidad](docs/observabilidad.md) — qué métricas se registran y por qué "generación" no es un contador de tiempo.
- [Aprendizajes](docs/aprendizajes.md) — checklist de qué se aprendió construyendo esto.
- [Despliegue](docs/despliegue.md) — runbook para subir el sitio estático al VPS.

## Desarrollo

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q --cov=provida --cov-report=term-missing   # 62 pruebas, 100% cobertura
```

## Demos

Cada uno demuestra un mecanismo específico y se puede correr de forma aislada:

```bash
python3 examples/demo_genoma_fijo.py           # VM ejecutando un genoma fijo
python3 examples/demo_autorreplicacion.py      # un organismo se copia a sí mismo
python3 examples/demo_mutacion.py              # mutación durante la copia
python3 examples/demo_poblacion.py             # una rejilla se llena de organismos
python3 examples/demo_tareas.py                # tareas lógicas como fuente de merit
python3 examples/demo_seleccion_natural.py     # selección natural emergente, verificada
python3 examples/demo_laboratorio.py           # gráficas: fitness, generación, árbol filogenético
python3 examples/demo_genoma_por_etiquetas.py  # auto-replicación sin conocer el tamaño del genoma
python3 examples/demo_evolucion_tamano.py      # el tamaño del genoma evoluciona vía indels
```

`demo_laboratorio.py` y `demo_evolucion_tamano.py` requieren `pip install -e ".[analisis]"`.

## Sitio estático

`sitio/generar.py` corre los experimentos de referencia y produce un reporte HTML con las gráficas — es lo que sirve [proVida.ibsen-soto.pro](https://proVida.ibsen-soto.pro). `sitio/Dockerfile` empaqueta ese build en una imagen Nginx sin dependencias de Python en la imagen final:

```bash
docker build -t provida-sitio -f sitio/Dockerfile .
docker run -p 8080:80 provida-sitio
```

## Autor

[Ibsen Soto Art](https://portafolio.ibsen-soto.pro) — aprendiz SENA de Análisis y Desarrollo de Software (ADSO), con formación previa en Biología.

## Licencia

Proyecto personal de aprendizaje / portafolio.
