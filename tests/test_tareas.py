"""Pruebas de humo para la Fase 4, sub-fase 5 (tareas lógicas / merit)."""

import random

from provida.tasks.ambiente import Ambiente
from provida.tasks.logicas import tareas_resueltas_por_output
from provida.vm.cpu import CPU
from provida.vm.instructions import MASCARA_REGISTRO, Instruccion as I

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
    I("nop", ()),
]


def test_tareas_resueltas_por_output_detecta_not():
    assert tareas_resueltas_por_output([5], (~5) & MASCARA_REGISTRO) == ["NOT"]


def test_tareas_resueltas_por_output_detecta_and_y_nand():
    a, b = 0b1100, 0b1010
    resultado = tareas_resueltas_por_output([a, b], a & b)
    assert resultado == ["AND"]
    resultado_nand = tareas_resueltas_por_output([a, b], (~(a & b)) & MASCARA_REGISTRO)
    assert resultado_nand == ["NAND"]


def test_tareas_resueltas_por_output_sin_historial_no_detecta_nada():
    assert tareas_resueltas_por_output([], 12345) == []


def test_sin_ambiente_input_output_no_tienen_efecto():
    cpu = CPU(GENOMA_TAREAS)  # sin ambiente
    cpu.run(9)
    assert cpu.merit == 1.0
    assert cpu.tareas_resueltas == set()
    assert cpu.ultimos_inputs == []


def test_organismo_resuelve_las_tres_tareas_y_el_merit_se_multiplica():
    cpu = CPU(GENOMA_TAREAS, rng=random.Random(11), ambiente=Ambiente())
    cpu.run(9)
    assert cpu.tareas_resueltas == {"NOT", "AND", "NAND"}
    assert cpu.merit == 2.0 * 4.0 * 8.0


def test_resolver_la_misma_tarea_dos_veces_no_duplica_el_bono():
    cpu = CPU(GENOMA_TAREAS, rng=random.Random(11), ambiente=Ambiente())
    cpu.run(9)  # resuelve las tres tareas una vez
    merit_tras_primera_vez = cpu.merit

    # Vuelve a emitir el mismo output (NAND) con el mismo historial de inputs.
    cpu.ip = 3  # instrucción "output AX"
    cpu.step()

    assert cpu.merit == merit_tras_primera_vez  # sin cambio: ya estaba acreditada


def test_cria_hereda_merit_y_tareas_ya_acreditadas_del_padre():
    from provida.world.grid import Mundo

    genoma_replicante_con_tareas = [
        I("h-alloc", ()),            # 0
        I("input", ("AX",)),         # 1
        I("input", ("BX",)),         # 2
        I("nand", ("AX", "BX")),     # 3
        I("output", ("AX",)),        # 4: resuelve NAND antes de replicarse
        I("inc", ("CX",)),           # 5
        I("add", ("CX", "CX")),      # 6
        I("add", ("CX", "CX")),      # 7
        I("inc", ("CX",)),           # 8
        I("add", ("CX", "CX")),      # 9
        I("add", ("CX", "CX")),      # 10   CX termina en 20 = len(genoma)
        I("nop", ()),                # 11   relleno: sin efecto sobre CX,
        I("nop", ()),                # 12   solo para que el tamaño del
        I("nop", ()),                # 13   contador cuadre exactamente
        I("nop", ()),                # 14   con el tamaño total del genoma
        I("jmp-if-zero", ("CX", 4)), # 15
        I("h-copy", ()),             # 16
        I("dec", ("CX",)),           # 17
        I("jmp", (-3,)),             # 18
        I("h-divide", ()),           # 19
    ]

    rng = random.Random(9)
    ambiente = Ambiente()
    mundo = Mundo(5, 5, rng=rng)
    padre = CPU(genoma_replicante_con_tareas, rng=rng, ambiente=ambiente)
    mundo.colocar(padre, 2, 2)

    turnos = 0
    while mundo.nacimientos < 1 and turnos < 2000:
        mundo.ejecutar_ciclo(instrucciones_por_turno=1)
        turnos += 1

    assert mundo.nacimientos == 1
    hijo = next(cpu for f, c, cpu in mundo.organismos_vivos() if (f, c) != (2, 2))
    assert hijo.merit == padre.merit
    assert hijo.tareas_resueltas == padre.tareas_resueltas
    assert hijo.ambiente is ambiente
