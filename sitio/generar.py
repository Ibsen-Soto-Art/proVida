"""Genera el sitio estático de proVida: corre los experimentos de referencia
y produce un reporte HTML con las gráficas, para servir como archivos
estáticos (ver sitio/Dockerfile).

Deliberadamente reutiliza los mismos genomas y semillas ya validados en
examples/demo_seleccion_natural.py, examples/demo_laboratorio.py y
examples/demo_evolucion_tamano.py -- este script no es un demo educativo
más, es el paso de build del sitio de producción, así que prioriza
reproducir resultados ya conocidos sobre explorar nuevos.
"""

import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from provida.metrics.registro import RegistroEventos
from provida.tasks.ambiente import Ambiente
from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I
from provida.world.grid import Mundo

RAIZ = Path(__file__).resolve().parent
BUILD = RAIZ / "build"
IMG = BUILD / "img"


def preparar_directorios() -> None:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    IMG.mkdir(parents=True)


# ---------------------------------------------------------------------------
# Experimento 1: selección natural + laboratorio (control vs. tarea)
# ---------------------------------------------------------------------------

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


def experimento_seleccion() -> dict:
    rng = random.Random(2026)
    ambiente = Ambiente()
    registro = RegistroEventos()
    mundo = Mundo(ancho=15, alto=15, rng=rng, registro=registro)
    for i, (fila, columna) in enumerate(POSICIONES):
        genoma = CONTROL if i % 2 == 0 else TAREA
        mundo.colocar(CPU(genoma, tasa_mutacion=0.0075, rng=rng, ambiente=ambiente), fila, columna)

    registro.registrar_snapshot(mundo.turno, mundo)
    while mundo.turno < 60_000:
        mundo.ejecutar_ciclos(2000, instrucciones_por_turno=3)
        registro.registrar_snapshot(mundo.turno, mundo)

    vivos = mundo.organismos_vivos()
    con_tarea = sum(1 for _, _, cpu in vivos if "NAND" in cpu.tareas_resueltas)

    # --- Gráfica: merit promedio y % con tarea, por turno ---
    df_snap = pd.DataFrame(registro.snapshots)
    df_snap["prop_nand"] = df_snap["conteo_tareas"].apply(lambda d: d.get("NAND", 0)) / df_snap["poblacion"]

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(df_snap["turno"], df_snap["merit_promedio"], color="#2563eb")
    ax1.set_xlabel("Turno")
    ax1.set_ylabel("Merit promedio de la población", color="#2563eb")
    ax1.tick_params(axis="y", labelcolor="#2563eb")
    ax2 = ax1.twinx()
    ax2.plot(df_snap["turno"], df_snap["prop_nand"] * 100, color="#ea580c")
    ax2.set_ylabel("% de la población con NAND resuelto", color="#ea580c")
    ax2.tick_params(axis="y", labelcolor="#ea580c")
    ax2.set_ylim(0, 105)
    ax1.set_title("Selección natural emergente: control vs. genotipo con tarea")
    fig.tight_layout()
    fig.savefig(IMG / "seleccion.png", dpi=130)
    plt.close(fig)

    # --- Gráfica: árbol filogenético simplificado ---
    eventos = registro.nacimientos[:40]
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
    colores = ["#ea580c" if grafo.nodes[n]["con_tarea"] else "#94a3b8" for n in grafo.nodes]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    nx.draw(
        grafo, pos=posiciones_grafo, ax=ax, node_color=colores, node_size=90,
        with_labels=False, arrows=False, width=0.6, edge_color="#e2e8f0",
    )
    ax.set_title(f"Árbol filogenético simplificado (primeros {len(eventos)} nacimientos)")
    fig.tight_layout()
    fig.savefig(IMG / "filogenia.png", dpi=130)
    plt.close(fig)

    return {"poblacion_final": len(vivos), "con_tarea_final": con_tarea}


# ---------------------------------------------------------------------------
# Experimento 2: evolución del tamaño del genoma (indels)
# ---------------------------------------------------------------------------

GENOMA_ANCESTRAL_POR_ETIQUETAS = [
    I("h-alloc", ()), I("nop-a", ()), I("h-copy", ()), I("jmp-vuelta-etiqueta", ()),
    I("nop-a", ()), I("jmp-etiqueta", ()), I("nop-c", ()), I("nop", ()),
    I("nop-b", ()), I("h-divide", ()),
]


def experimento_tamano_genoma() -> dict:
    rng = random.Random(7)
    mundo = Mundo(ancho=12, alto=12, rng=rng)
    mundo.colocar(
        CPU(GENOMA_ANCESTRAL_POR_ETIQUETAS, tasa_mutacion=0.0075, tasa_insercion=0.01, tasa_delecion=0.01, rng=rng),
        fila=6, columna=6,
    )
    turnos, promedios, minimos, maximos = [], [], [], []
    while mundo.turno < 100_000:
        mundo.ejecutar_ciclos(2000, instrucciones_por_turno=3)
        longitudes = [len(cpu.genoma) for _, _, cpu in mundo.organismos_vivos()]
        if longitudes:
            turnos.append(mundo.turno)
            promedios.append(sum(longitudes) / len(longitudes))
            minimos.append(min(longitudes))
            maximos.append(max(longitudes))

    longitud_original = len(GENOMA_ANCESTRAL_POR_ETIQUETAS)
    longitudes_finales = [len(cpu.genoma) for _, _, cpu in mundo.organismos_vivos()]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(turnos, promedios, color="#2563eb", label="Promedio")
    ax.fill_between(turnos, minimos, maximos, color="#2563eb", alpha=0.15, label="Rango (mín-máx)")
    ax.axhline(longitud_original, color="#94a3b8", linestyle="--", linewidth=1, label="Longitud del ancestro")
    ax.set_xlabel("Turno")
    ax.set_ylabel("Longitud del genoma (instrucciones)")
    ax.set_title("Evolución del tamaño del genoma con inserción/deleción")
    ax.legend()
    fig.tight_layout()
    fig.savefig(IMG / "tamano_genoma.png", dpi=130)
    plt.close(fig)

    distribucion = sorted(Counter(longitudes_finales).items())
    return {"longitud_original": longitud_original, "distribucion": distribucion, "poblacion": len(longitudes_finales)}


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

def generar_html(resultado_seleccion: dict, resultado_tamano: dict) -> str:
    pct_final = 100 * resultado_seleccion["con_tarea_final"] / resultado_seleccion["poblacion_final"]
    dist_str = ", ".join(f"{n} instr. × {c}" for n, c in resultado_tamano["distribucion"])

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>proVida — simulador de vida digital</title>
<style>
  :root {{
    --bg: #0b1220; --panel: #121b2e; --text: #e2e8f0; --muted: #94a3b8;
    --accent: #ea580c; --accent2: #2563eb; --border: #1f2b45;
    --font-body: -apple-system, "Segoe UI", Roboto, sans-serif;
    --font-mono: ui-monospace, "SF Mono", "Cascadia Code", Consolas, monospace;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: var(--font-body);
    background: var(--bg); color: var(--text); line-height: 1.6;
  }}
  a {{ color: var(--accent2); }}
  a:focus-visible, button:focus-visible {{ outline: 2px solid var(--accent2); outline-offset: 2px; border-radius: 3px; }}
  header {{ padding: 4rem 1.5rem 2rem; text-align: center; }}
  header h1 {{
    font-family: var(--font-mono); font-size: 2.6rem; margin: 0 0 0.6rem;
    letter-spacing: -0.02em; text-wrap: balance;
  }}
  header p {{ color: var(--muted); max-width: 620px; margin: 0 auto; font-size: 1.05rem; text-wrap: balance; }}
  main {{ max-width: 880px; margin: 0 auto; padding: 1rem 1.5rem 4rem; display: flex; flex-direction: column; gap: 1.5rem; }}
  section {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 12px;
    padding: 1.75rem;
  }}
  section h2 {{ margin: 0 0 0.9rem; font-size: 1.35rem; text-wrap: balance; }}
  section h2 .tag {{
    color: var(--accent); font-family: var(--font-mono); font-weight: 600; font-size: 0.78rem;
    text-transform: uppercase; letter-spacing: 0.08em; display: block; margin-bottom: 0.4rem;
  }}
  section > p {{ max-width: 65ch; }}
  img {{ max-width: 100%; border-radius: 8px; border: 1px solid var(--border); display: block; margin: 1rem 0; }}
  .stat-row {{ display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0 0; }}
  .stat {{ background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 0.9rem 1.2rem; flex: 1; min-width: 160px; }}
  .stat .n {{ font-family: var(--font-mono); font-variant-numeric: tabular-nums; font-size: 1.7rem; font-weight: 700; color: var(--accent2); }}
  .stat .l {{ color: var(--muted); font-size: 0.85rem; margin-top: 0.2rem; }}
  code {{ font-family: var(--font-mono); background: var(--bg); padding: 0.15em 0.4em; border-radius: 4px; font-size: 0.85em; border: 1px solid var(--border); }}
  footer {{ text-align: center; color: var(--muted); padding: 2rem; font-size: 0.9rem; }}
</style>
</head>
<body>
<header>
  <h1>proVida</h1>
  <p>Simulador de vida digital inspirado en Avida — organismos autorreplicantes que compiten, mutan y evolucionan dentro de una máquina virtual propia, construido desde cero como proyecto de aprendizaje.</p>
</header>
<main>

<section>
  <h2><span class="tag">Hallazgo 1</span>Selección natural emergente</h2>
  <p>Dos genotipos de exactamente la misma longitud compiten por el mismo espacio finito: uno resuelve una tarea lógica (NAND, merit ×8), el otro no. Ningún código declara quién debe ganar — el resultado es una consecuencia del planificador ponderado por merit.</p>
  <div class="stat-row">
    <div class="stat"><div class="n">{pct_final:.1f}%</div><div class="l">población final con la tarea resuelta (partiendo de 50%)</div></div>
    <div class="stat"><div class="n">{resultado_seleccion['poblacion_final']}</div><div class="l">organismos vivos al cierre del experimento</div></div>
  </div>
  <img src="img/seleccion.png" alt="Evolución del merit promedio y del porcentaje con NAND resuelto por turno">
</section>

<section>
  <h2><span class="tag">Hallazgo 2</span>Árbol filogenético simplificado</h2>
  <p>Los primeros 40 nacimientos del experimento anterior, coloreados por linaje. Desde la segunda generación, casi toda la descendencia visible desciende del genotipo con tarea.</p>
  <img src="img/filogenia.png" alt="Árbol filogenético simplificado de los primeros 40 nacimientos">
</section>

<section>
  <h2><span class="tag">Hallazgo 3</span>Evolución del tamaño del genoma</h2>
  <p>Con direccionamiento por contenido (nop-labels) en vez de saltos numéricos, el genoma puede crecer o encoger vía inserción/deleción sin romper el mecanismo de auto-replicación. Tras 100 000 turnos, el tamaño del genoma dejó de ser una constante.</p>
  <div class="stat-row">
    <div class="stat"><div class="n">{resultado_tamano['longitud_original']}</div><div class="l">instrucciones del genoma ancestral</div></div>
    <div class="stat"><div class="n">{resultado_tamano['poblacion']}</div><div class="l">organismos en la distribución final</div></div>
  </div>
  <img src="img/tamano_genoma.png" alt="Evolución del tamaño del genoma con inserción/deleción activas">
  <p style="color:var(--muted); font-size:0.9rem;">Distribución final: <code>{dist_str}</code></p>
</section>

<section>
  <h2><span class="tag">Proyecto</span>Cómo está construido</h2>
  <p>Python puro (sin dependencias externas para el núcleo). Una VM con registros de 32 bits, pila y punteros de instrucción; auto-replicación instrucción por instrucción; mutación por sustitución/inserción/deleción; un mundo espacial toroidal con planificador ponderado por merit; tareas lógicas como fuente de recompensa metabólica.</p>
  <p>Documentación completa (visión técnica, arquitectura, glosario, estrategia de testing, observabilidad) y código fuente en <a href="https://github.com/Ibsen-Soto-Art/proVida">github.com/Ibsen-Soto-Art/proVida</a>.</p>
</section>

</main>
<footer>proVida — proyecto de aprendizaje de Ibsen Soto Art · <a href="https://github.com/Ibsen-Soto-Art/proVida">código fuente</a></footer>
</body>
</html>
"""


def main() -> None:
    preparar_directorios()
    resultado_seleccion = experimento_seleccion()
    resultado_tamano = experimento_tamano_genoma()
    (BUILD / "index.html").write_text(generar_html(resultado_seleccion, resultado_tamano), encoding="utf-8")
    print(f"Sitio generado en {BUILD}")


if __name__ == "__main__":
    main()
