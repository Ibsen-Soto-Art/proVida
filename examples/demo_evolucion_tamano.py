"""Demo de la Fase 7: evolución del tamaño del genoma vía indels.

Usa el genoma ancestral por etiquetas (examples/demo_genoma_por_etiquetas.py)
-- el único que puede tolerar cambios de tamaño, porque su bucle de copia
no depende de contar instrucciones. Con inserción y deleción activas,
el tamaño del genoma de la población deja de ser una constante y se
vuelve algo que EVOLUCIONA.

No hay tareas lógicas en este experimento (merit uniforme para todos) --
a propósito, para observar la deriva de tamaño de forma aislada, sin
mezclarla con presión de selección por tareas.
"""

import random
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I
from provida.world.grid import Mundo

GENOMA_ANCESTRAL_POR_ETIQUETAS = [
    I("h-alloc", ()),
    I("nop-a", ()),
    I("h-copy", ()),
    I("jmp-vuelta-etiqueta", ()),
    I("nop-a", ()),
    I("jmp-etiqueta", ()),
    I("nop-c", ()),
    I("nop", ()),
    I("nop-b", ()),
    I("h-divide", ()),
]
LONGITUD_ORIGINAL = len(GENOMA_ANCESTRAL_POR_ETIQUETAS)

SALIDA = Path(__file__).resolve().parent.parent / "runs"
SALIDA.mkdir(exist_ok=True)

rng = random.Random(7)
mundo = Mundo(ancho=12, alto=12, rng=rng)
mundo.colocar(
    CPU(
        GENOMA_ANCESTRAL_POR_ETIQUETAS,
        tasa_mutacion=0.0075,
        tasa_insercion=0.01,
        tasa_delecion=0.01,
        rng=rng,
    ),
    fila=6,
    columna=6,
)

CHECKPOINT = 2000
TOTAL_TURNOS = 100_000
turnos, promedios, minimos, maximos = [], [], [], []

while mundo.turno < TOTAL_TURNOS:
    mundo.ejecutar_ciclos(CHECKPOINT, instrucciones_por_turno=3)
    longitudes = [len(cpu.genoma) for _, _, cpu in mundo.organismos_vivos()]
    if longitudes:
        turnos.append(mundo.turno)
        promedios.append(sum(longitudes) / len(longitudes))
        minimos.append(min(longitudes))
        maximos.append(max(longitudes))

print(f"Turnos totales: {mundo.turno}  población final: {mundo.poblacion_actual()}")

longitudes_finales = [len(cpu.genoma) for _, _, cpu in mundo.organismos_vivos()]
from collections import Counter

distribucion = sorted(Counter(longitudes_finales).items())
print(f"Longitud original del ancestro: {LONGITUD_ORIGINAL}")
print("Distribución final de longitudes (longitud: cantidad):", distribucion)
en_longitud_original = longitudes_finales.count(LONGITUD_ORIGINAL)
print(
    f"{en_longitud_original}/{len(longitudes_finales)} organismos siguen exactamente "
    f"en la longitud original ({100 * en_longitud_original / len(longitudes_finales):.0f}%)"
)

# --- Gráfica: promedio/mínimo/máximo de longitud del genoma por turno ---
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(turnos, promedios, color="tab:blue", label="Promedio")
ax.fill_between(turnos, minimos, maximos, color="tab:blue", alpha=0.15, label="Rango (mín-máx)")
ax.axhline(LONGITUD_ORIGINAL, color="gray", linestyle="--", linewidth=1, label="Longitud del ancestro")
ax.set_xlabel("Turno")
ax.set_ylabel("Longitud del genoma (instrucciones)")
ax.set_title("Evolución del tamaño del genoma con inserción/deleción activas")
ax.legend()
fig.tight_layout()
fig.savefig(SALIDA / "04_evolucion_tamano_genoma.png", dpi=120)
plt.close(fig)
print("\nGráfica guardada en:", SALIDA / "04_evolucion_tamano_genoma.png")
