"""Prueba central de la Fase 4, sub-fase 6: la selección natural emerge.

Dos genotipos de la MISMA longitud (20 instrucciones) compiten por el
mismo espacio finito. La única diferencia funcional es que uno resuelve
NAND (merit x8) y el otro no. Si el sistema está bien construido, el
genotipo con tarea debería terminar dominando la población -- no porque
el código lo declare, sino como consecuencia de que el planificador
reparte turnos de CPU proporcional al merit.

Se incluye también un control nulo: la misma carrera, pero sin ambiente
(nadie puede ganar merit) y sin mutación. Si el mecanismo de selección
fuera un artefacto de otra cosa (por ejemplo, que las instrucciones
input/output/nand tuvieran alguna ventaja oculta de ejecución), también
se vería una dominancia en el control. No debería verse -- la proporción
debe quedarse cerca de 50/50, dentro del ruido esperado por deriva
genética en una población finita.
"""

import random

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

POSICIONES_INICIALES = [(2, 2), (2, 12), (12, 2), (12, 12), (7, 3), (3, 7), (11, 7), (7, 11)]


def _sembrar(mundo: Mundo, tasa_mutacion: float, ambiente: Ambiente | None) -> None:
    for i, (fila, columna) in enumerate(POSICIONES_INICIALES):
        genoma = CONTROL if i % 2 == 0 else TAREA
        mundo.colocar(
            CPU(genoma, tasa_mutacion=tasa_mutacion, rng=mundo.rng, ambiente=ambiente),
            fila,
            columna,
        )


def test_genomas_control_y_tarea_tienen_la_misma_longitud():
    # Requisito del experimento: si difieren en tamaño, una ventaja
    # observada podría deberse solo a copiarse más rápido, no al merit.
    assert len(CONTROL) == len(TAREA)


def test_el_genotipo_con_tarea_termina_dominando_la_poblacion():
    rng = random.Random(2026)
    ambiente = Ambiente()
    mundo = Mundo(ancho=15, alto=15, rng=rng)
    _sembrar(mundo, tasa_mutacion=0.0075, ambiente=ambiente)

    mundo.ejecutar_ciclos(100_000, instrucciones_por_turno=3)

    vivos = mundo.organismos_vivos()
    con_tarea = sum(1 for _, _, cpu in vivos if "NAND" in cpu.tareas_resueltas)
    porcentaje = 100 * con_tarea / len(vivos)

    # Empezó en 50/50 (4 y 4). Un resultado > 90% no puede explicarse por
    # azar puro en una rejilla de 225 celdas -- es selección direccional.
    assert porcentaje > 90.0


def test_control_nulo_sin_ambiente_ni_mutacion_no_produce_dominancia():
    # Mismo experimento, pero sin ambiente (nadie gana merit nunca) y sin
    # mutación (los genomas no cambian). Si el resultado anterior fuera un
    # artefacto -- por ejemplo, que las instrucciones input/output/nand
    # tuvieran alguna ventaja de ejecución que nada tiene que ver con
    # merit -- se vería una dominancia también aquí. No debería.
    rng = random.Random(1)
    mundo = Mundo(ancho=15, alto=15, rng=rng)
    _sembrar(mundo, tasa_mutacion=0.0, ambiente=None)

    mundo.ejecutar_ciclos(100_000, instrucciones_por_turno=3)

    vivos = mundo.organismos_vivos()
    tarea_por_genoma = sum(1 for _, _, cpu in vivos if cpu.genoma == TAREA)
    porcentaje = 100 * tarea_por_genoma / len(vivos)

    # Tolerancia amplia: deriva genética en población finita puede mover
    # la proporción, pero no debería acercarse a la dominancia casi total
    # (>90%) que sí se observa cuando el merit está activo.
    assert 25.0 < porcentaje < 75.0
