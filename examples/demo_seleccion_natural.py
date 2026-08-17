"""Demo de la Fase 4, sub-fase 6: verificar que la selección natural emerge.

Este es el experimento central del MVP. Junta todo lo construido en las
sub-fases anteriores (población + mutación + tareas) para responder una
pregunta concreta: si dos genotipos de la MISMA longitud (para que
ninguno tenga ventaja solo por copiarse más rápido) compiten por el mismo
espacio, ¿el que resuelve una tarea lógica (y por tanto tiene más merit)
termina representando una proporción creciente de la población?

Ningún fragmento de código de este archivo, ni de provida/world/grid.py,
"decide" que el genotipo con tarea debe ganar. Solo existe: (a) un
planificador que reparte turnos de CPU proporcional al merit, y (b) un
mecanismo que multiplica el merit al resolver una tarea. La dominancia
observada abajo es una CONSECUENCIA de esas dos reglas, no una regla en
sí misma -- eso es lo que hace que sea selección natural "emergente" y no
una simulación con el resultado escrito de antemano.
"""

import random

from provida.tasks.ambiente import Ambiente
from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I
from provida.world.grid import Mundo

# Genotipo CONTROL: se auto-replica, nunca gana merit (sin input/output/nand).
CONTROL = [
    I("h-alloc", ()), I("nop", ()), I("nop", ()), I("nop", ()), I("nop", ()),
    I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
    I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
    I("nop", ()), I("nop", ()), I("nop", ()), I("nop", ()),
    I("jmp-if-zero", ("CX", 4)), I("h-copy", ()), I("dec", ("CX",)),
    I("jmp", (-3,)), I("h-divide", ()),
]

# Genotipo TAREA: idéntica longitud (20 instrucciones), pero resuelve NAND
# antes de dividirse -> merit x8 la primera vez que lo logra.
TAREA = [
    I("h-alloc", ()), I("input", ("AX",)), I("input", ("BX",)),
    I("nand", ("AX", "BX")), I("output", ("AX",)),
    I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
    I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
    I("nop", ()), I("nop", ()), I("nop", ()), I("nop", ()),
    I("jmp-if-zero", ("CX", 4)), I("h-copy", ()), I("dec", ("CX",)),
    I("jmp", (-3,)), I("h-divide", ()),
]

assert len(CONTROL) == len(TAREA) == 20, "misma longitud: la única ventaja debe venir del merit"

ANCHO, ALTO = 15, 15
CAPACIDAD = ANCHO * ALTO

rng = random.Random(2026)
ambiente = Ambiente()
mundo = Mundo(ancho=ANCHO, alto=ALTO, rng=rng)

# 4 organismos de cada genotipo, en posiciones simétricas -- ningún
# genotipo empieza con ventaja posicional.
posiciones = [(2, 2), (2, 12), (12, 2), (12, 12), (7, 3), (3, 7), (11, 7), (7, 11)]
for i, (fila, columna) in enumerate(posiciones):
    genoma = CONTROL if i % 2 == 0 else TAREA
    mundo.colocar(CPU(genoma, tasa_mutacion=0.0075, rng=rng, ambiente=ambiente), fila, columna)

print(f"Rejilla {ANCHO}x{ALTO}. Inicio: 4 'control' + 4 'tarea' (50% / 50%).\n")

turno = 0
for objetivo in [10000, 30000, 50000, 70000, 90000, 100000]:
    mundo.ejecutar_ciclos(objetivo - turno, instrucciones_por_turno=3)
    turno = objetivo
    vivos = mundo.organismos_vivos()
    con_tarea = sum(1 for _, _, cpu in vivos if "NAND" in cpu.tareas_resueltas)
    porcentaje = 100 * con_tarea / len(vivos) if vivos else 0
    print(
        f"turno {turno:6}: población = {len(vivos):3}/{CAPACIDAD}  "
        f"con tarea = {con_tarea:3} ({porcentaje:5.1f}%)"
    )

vivos_final = mundo.organismos_vivos()
con_tarea_final = sum(1 for _, _, cpu in vivos_final if "NAND" in cpu.tareas_resueltas)
porcentaje_final = 100 * con_tarea_final / len(vivos_final)

print(
    f"\nEl genotipo 'tarea' pasó de 50% a {porcentaje_final:.1f}% de la población, "
    "partiendo de un empate numérico inicial. Este es el fenómeno de "
    "'exclusión competitiva' de la ecología de poblaciones: cuando dos "
    "especies compiten por el mismo recurso limitado (aquí, espacio en la "
    "rejilla), la que tiene incluso una ventaja moderada tiende a "
    "desplazar completamente a la otra -- no a coexistir en proporciones "
    "estables."
)

assert porcentaje_final > 95.0
