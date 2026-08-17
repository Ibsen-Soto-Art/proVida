"""Demo de la Fase 4, sub-fase 4: una población en un mundo espacial.

Mutación deliberadamente APAGADA en esta demo (tasa_mutacion=0.0): el
objetivo es observar, de forma aislada, la dinámica puramente espacial
-- crecimiento de la población desde un solo organismo hasta llenar la
rejilla, y el "recambio" de individuos una vez que ya no hay espacio
vacío -- sin mezclarla todavía con variación genética. Esa combinación
(población + mutación + selección real) llega en la sub-fase 6, una vez
que la sub-fase 5 le dé sentido al merit.
"""

import random

from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I
from provida.world.grid import Mundo

GENOMA_ANCESTRAL = [
    I("h-alloc", ()),
    I("inc", ("CX",)),
    I("add", ("CX", "CX")),
    I("inc", ("CX",)),
    I("add", ("CX", "CX")),
    I("add", ("CX", "CX")),
    I("inc", ("CX",)),
    I("jmp-if-zero", ("CX", 4)),
    I("h-copy", ()),
    I("dec", ("CX",)),
    I("jmp", (-3,)),
    I("h-divide", ()),
    I("nop", ()),
]

ANCHO, ALTO = 10, 10
CAPACIDAD = ANCHO * ALTO

rng = random.Random(2026)
mundo = Mundo(ancho=ANCHO, alto=ALTO, rng=rng)
mundo.colocar(CPU(GENOMA_ANCESTRAL, rng=rng), fila=ALTO // 2, columna=ANCHO // 2)

print(f"Rejilla {ANCHO}x{ALTO} (capacidad: {CAPACIDAD} organismos). Empezando con 1.")

puntos_de_control = [50, 200, 500, 1000, 3000, 6000, 10000, 15000, 20000, 25000]
turno = 0
for objetivo in puntos_de_control:
    mundo.ejecutar_ciclos(objetivo - turno, instrucciones_por_turno=3)
    turno = objetivo
    print(
        f"Turno {turno:5}: población = {mundo.poblacion_actual():3}/{CAPACIDAD}  "
        f"nacimientos acumulados = {mundo.nacimientos:4}  "
        f"reemplazos acumulados = {mundo.reemplazos:4}"
    )

assert mundo.poblacion_actual() == CAPACIDAD, "la rejilla debería haberse llenado"
assert mundo.reemplazos > 0, "una vez llena, los nacimientos deberían reemplazar a alguien"
print("\nLa rejilla se llenó y el recambio de individuos sigue ocurriendo después de eso.")

print(
    "\nNota: el crecimiento se frena solo, sin que nadie haya programado un "
    "'límite de capacidad' explícito -- es consecuencia directa de que el "
    "planificador reparte turnos entre TODOS los organismos vivos por igual: "
    "cuantos más hay, menos turnos le tocan a cada uno, y más tarda cada uno "
    "en completar su propia replicación. Es una curva de crecimiento "
    "logística emergente, el mismo patrón que en ecología de poblaciones "
    "reales con recursos limitados."
)
