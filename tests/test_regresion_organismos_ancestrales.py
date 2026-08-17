"""Pruebas de regresión de la Fase 5: organismos de referencia "congelados".

A diferencia de las pruebas de humo de las sub-fases 1-6 (que verifican
propiedades generales, ej. "la cría es idéntica al padre"), estas pruebas
fijan NÚMEROS EXACTOS observados en corridas conocidas de organismos de
referencia. El objetivo no es solo "el comportamiento es razonable" sino
"el comportamiento es EXACTAMENTE este, y si cambia, algo se movió" --
aunque el cambio sea sutil y no rompa ninguna otra prueba (por ejemplo,
un refactor que altere el orden en que se consumen números aleatorios del
generador, produciendo mutaciones distintas para la misma semilla).

Si una de estas pruebas falla tras un cambio intencional (ej. se ajustó
a propósito el orden de las tiradas aleatorias), hay que actualizar el
valor esperado a mano, entendiendo por qué cambió -- no es un fallo a
ignorar.
"""

import random

from provida.tasks.ambiente import Ambiente
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

GENOMA_TAREAS = [
    I("input", ("AX",)),
    I("input", ("BX",)),
    I("nand", ("AX", "BX")),
    I("output", ("AX",)),
    I("mov", ("CX", "AX")),
    I("nand", ("CX", "CX")),
    I("output", ("CX",)),
    I("nand", ("BX", "BX")),
    I("output", ("BX",)),
]


def test_regresion_ancestro_se_replica_en_exactamente_61_pasos():
    cpu = CPU(GENOMA_ANCESTRAL)
    pasos = cpu.run_hasta_replicar(max_pasos=200)
    assert pasos == 61
    assert cpu.genoma_hijo == GENOMA_ANCESTRAL


def test_regresion_mutacion_con_semilla_7_produce_esta_mutacion_exacta():
    # Semilla y tasa fijas (0.05) conocidas desde la sub-fase 3: la única
    # mutación cae sobre la instrucción h-copy (índice 8). El opcode
    # exacto en el que se convierte depende de CUÁNTOS opcodes hay en el
    # set (rng.choice sobre una lista más larga mapea la misma tirada a
    # otro resultado) -- cambió de `push BX` a `input BX` en la Fase 7,
    # al agregar las instrucciones de etiqueta. Es un cambio esperado y
    # documentado, no una regresión real: la mutación sigue cayendo en el
    # mismo sitio (h-copy) y sigue siendo letal para la auto-replicación
    # de la cría -- la narrativa de "mutación letal" se mantiene.
    cpu = CPU(GENOMA_ANCESTRAL, tasa_mutacion=0.05, rng=random.Random(7))
    cpu.run_hasta_replicar(max_pasos=200)

    assert cpu.mutaciones_ocurridas == 1
    assert cpu.genoma_hijo[8] == I("input", ("BX",))
    # El resto del genoma debe seguir intacto.
    esperado = list(GENOMA_ANCESTRAL)
    esperado[8] = I("input", ("BX",))
    assert cpu.genoma_hijo == esperado


def test_regresion_organismo_de_tareas_con_semilla_11():
    cpu = CPU(GENOMA_TAREAS, rng=random.Random(11), ambiente=Ambiente())
    cpu.run(9)

    assert cpu.tareas_resueltas == {"NOT", "AND", "NAND"}
    assert cpu.merit == 64.0  # 2.0 (NOT) * 4.0 (AND) * 8.0 (NAND)


def test_regresion_experimento_de_seleccion_con_semilla_2026():
    control = [
        I("h-alloc", ()), I("nop", ()), I("nop", ()), I("nop", ()), I("nop", ()),
        I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
        I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
        I("nop", ()), I("nop", ()), I("nop", ()), I("nop", ()),
        I("jmp-if-zero", ("CX", 4)), I("h-copy", ()), I("dec", ("CX",)),
        I("jmp", (-3,)), I("h-divide", ()),
    ]
    tarea = [
        I("h-alloc", ()), I("input", ("AX",)), I("input", ("BX",)),
        I("nand", ("AX", "BX")), I("output", ("AX",)),
        I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
        I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
        I("nop", ()), I("nop", ()), I("nop", ()), I("nop", ()),
        I("jmp-if-zero", ("CX", 4)), I("h-copy", ()), I("dec", ("CX",)),
        I("jmp", (-3,)), I("h-divide", ()),
    ]
    posiciones = [(2, 2), (2, 12), (12, 2), (12, 12), (7, 3), (3, 7), (11, 7), (7, 11)]

    rng = random.Random(2026)
    ambiente = Ambiente()
    mundo = Mundo(ancho=15, alto=15, rng=rng)
    for i, (fila, columna) in enumerate(posiciones):
        genoma = control if i % 2 == 0 else tarea
        mundo.colocar(CPU(genoma, tasa_mutacion=0.0075, rng=rng, ambiente=ambiente), fila, columna)

    mundo.ejecutar_ciclos(100_000, instrucciones_por_turno=3)

    vivos = mundo.organismos_vivos()
    con_tarea = sum(1 for _, _, cpu in vivos if "NAND" in cpu.tareas_resueltas)

    # Valores exactos observados al construir la demo de la sub-fase 6:
    # con esta semilla, a los 100k turnos la rejilla está totalmente
    # saturada y el genotipo con tarea desplazó por completo al control.
    assert len(vivos) == 225
    assert con_tarea == 225
