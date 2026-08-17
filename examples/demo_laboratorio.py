"""Demo de la Fase 6: el "laboratorio" -- observar la evolución con datos.

Corre el mismo experimento de competencia de la sub-fase 6 (control vs.
tarea), pero esta vez con un RegistroEventos conectado al Mundo, y
produce tres gráficas a partir de esos datos crudos:

  1. Evolución del merit promedio de la población y del % que resolvió
     NAND, a lo largo del tiempo (turnos).
  2. Fitness (merit) promedio al nacer, agrupado por generación --
     usando "generación" como profundidad de linaje (ver docs/glosario.md),
     no como un contador de tiempo sincronizado.
  3. Un árbol filogenético simplificado de los primeros ~40 nacimientos,
     coloreado por si ese organismo ya tenía NAND resuelto al nacer.

Requiere las dependencias opcionales de análisis: `pip install -e ".[analisis]"`.
"""

import random
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sin pantalla disponible: guardamos a archivo directamente
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from provida.metrics.registro import RegistroEventos
from provida.tasks.ambiente import Ambiente
from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I
from provida.world.grid import Mundo

CONTROL = [
    I("h-alloc", ()), I("nop", ()), I("nop", ()), I("nop", ()), I("nop", ()),
    I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
    I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
    I("nop", ()), I("nop", ()), I("nop", ()), I("nop", ()),
    I("jmp-if-zero", ("CX", 4)), I("h-copy", ()), I("dec", ("CX",)),
    I("jmp", (-3,)), I("h-divide", ()),
]
TAREA = [
    I("h-alloc", ()), I("input", ("AX",)), I("input", ("BX",)),
    I("nand", ("AX", "BX")), I("output", ("AX",)),
    I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
    I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
    I("nop", ()), I("nop", ()), I("nop", ()), I("nop", ()),
    I("jmp-if-zero", ("CX", 4)), I("h-copy", ()), I("dec", ("CX",)),
    I("jmp", (-3,)), I("h-divide", ()),
]
POSICIONES = [(2, 2), (2, 12), (12, 2), (12, 12), (7, 3), (3, 7), (11, 7), (7, 11)]

SALIDA = Path(__file__).resolve().parent.parent / "runs"
SALIDA.mkdir(exist_ok=True)

rng = random.Random(2026)
ambiente = Ambiente()
registro = RegistroEventos()
mundo = Mundo(ancho=15, alto=15, rng=rng, registro=registro)

for i, (fila, columna) in enumerate(POSICIONES):
    genoma = CONTROL if i % 2 == 0 else TAREA
    mundo.colocar(CPU(genoma, tasa_mutacion=0.0075, rng=rng, ambiente=ambiente), fila, columna)

CHECKPOINT = 2000
TOTAL_TURNOS = 60000

registro.registrar_snapshot(mundo.turno, mundo)
while mundo.turno < TOTAL_TURNOS:
    mundo.ejecutar_ciclos(CHECKPOINT, instrucciones_por_turno=3)
    registro.registrar_snapshot(mundo.turno, mundo)

print(f"Turnos totales: {mundo.turno}  población final: {mundo.poblacion_actual()}")
print(f"Nacimientos registrados: {len(registro.nacimientos)}")

# --- Gráfica 1: merit promedio y % con NAND resuelto, por turno ---
df_snap = pd.DataFrame(registro.snapshots)
df_snap["prop_nand"] = df_snap["conteo_tareas"].apply(lambda d: d.get("NAND", 0)) / df_snap["poblacion"]

fig, ax1 = plt.subplots(figsize=(8, 5))
ax1.plot(df_snap["turno"], df_snap["merit_promedio"], color="tab:blue")
ax1.set_xlabel("Turno")
ax1.set_ylabel("Merit promedio de la población", color="tab:blue")
ax1.tick_params(axis="y", labelcolor="tab:blue")

ax2 = ax1.twinx()
ax2.plot(df_snap["turno"], df_snap["prop_nand"] * 100, color="tab:orange")
ax2.set_ylabel("% de la población con NAND resuelto", color="tab:orange")
ax2.tick_params(axis="y", labelcolor="tab:orange")
ax2.set_ylim(0, 105)

plt.title("Evolución del fitness promedio y de la tarea NAND en la población")
fig.tight_layout()
fig.savefig(SALIDA / "01_fitness_y_tareas_por_turno.png", dpi=120)
plt.close(fig)

# --- Gráfica 2: fitness promedio por generación (profundidad de linaje) ---
df_nac = pd.DataFrame(registro.nacimientos)
fitness_por_generacion = df_nac.groupby("generacion")["merit"].mean()

fig, ax = plt.subplots(figsize=(8, 5))
fitness_por_generacion.plot(ax=ax, marker="o", color="tab:green")
ax.set_xlabel("Generación (profundidad de linaje desde el fundador)")
ax.set_ylabel("Merit promedio al nacer")
ax.set_title("Fitness promedio por generación")
fig.tight_layout()
fig.savefig(SALIDA / "02_fitness_por_generacion.png", dpi=120)
plt.close(fig)

# --- Gráfica 3: árbol filogenético simplificado (primeros 40 nacimientos) ---
PRIMEROS_N = 40
eventos = registro.nacimientos[:PRIMEROS_N]

grafo = nx.DiGraph()
for i in range(len(POSICIONES)):
    grafo.add_node(i, generacion=0, con_tarea=(i % 2 == 1))

for evento in eventos:
    grafo.add_node(evento["id"], generacion=evento["generacion"], con_tarea=("NAND" in evento["tareas_resueltas"]))
    if evento["id_padre"] in grafo:
        grafo.add_edge(evento["id_padre"], evento["id"])

por_generacion = defaultdict(list)
for nodo, datos in grafo.nodes(data=True):
    por_generacion[datos["generacion"]].append(nodo)

posiciones_grafo = {}
for gen, nodos in por_generacion.items():
    nodos_ordenados = sorted(nodos)
    n = len(nodos_ordenados)
    for idx, nodo in enumerate(nodos_ordenados):
        posiciones_grafo[nodo] = (idx - (n - 1) / 2, -gen)

colores = ["tab:orange" if grafo.nodes[n]["con_tarea"] else "tab:gray" for n in grafo.nodes]

fig, ax = plt.subplots(figsize=(11, 6))
nx.draw(
    grafo,
    pos=posiciones_grafo,
    ax=ax,
    node_color=colores,
    node_size=90,
    with_labels=False,
    arrows=False,
    width=0.6,
    edge_color="lightgray",
)
ax.set_title(
    f"Árbol filogenético simplificado (primeros {len(eventos)} nacimientos)\n"
    "naranja = linaje con NAND resuelto  ·  gris = sin tarea resuelta"
)
fig.tight_layout()
fig.savefig(SALIDA / "03_arbol_filogenetico.png", dpi=120)
plt.close(fig)

print("\nGráficas guardadas en:", SALIDA)
for archivo in sorted(SALIDA.glob("*.png")):
    print(" -", archivo.name)
