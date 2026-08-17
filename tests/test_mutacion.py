"""Pruebas de humo para la Fase 4, sub-fase 3 (mutación por sustitución)."""

import random

from provida.mutation.sustitucion import copiar_con_mutacion, instruccion_aleatoria
from provida.vm.cpu import CPU
from provida.vm.instructions import ARIDAD_OPCODES, Instruccion as I


def test_instruccion_aleatoria_respeta_la_aridad_de_cada_opcode():
    rng = random.Random(0)
    # Muchas muestras para tener buena probabilidad de tocar todos los opcodes.
    for _ in range(500):
        instr = instruccion_aleatoria(rng, longitud_genoma=20)
        assert instr.opcode in ARIDAD_OPCODES
        assert len(instr.args) == ARIDAD_OPCODES[instr.opcode]


def test_tasa_cero_nunca_muta():
    rng = random.Random(0)
    original = I("inc", ("AX",))
    for _ in range(200):
        resultado, hubo_mutacion = copiar_con_mutacion(original, 0.0, 10, rng)
        assert resultado == original
        assert hubo_mutacion is False


def test_tasa_uno_siempre_intenta_mutar():
    rng = random.Random(0)
    original = I("inc", ("AX",))
    for _ in range(200):
        _, hubo_mutacion = copiar_con_mutacion(original, 1.0, 10, rng)
        assert hubo_mutacion is True


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


def test_cpu_con_tasa_cero_replica_identico_por_defecto():
    # Regresión: sin pasar tasa_mutacion, el comportamiento debe ser
    # exactamente el de la sub-fase 2 (copia exacta).
    cpu = CPU(GENOMA_ANCESTRAL)
    cpu.run_hasta_replicar(max_pasos=200)
    assert cpu.genoma_hijo == cpu.genoma
    assert cpu.mutaciones_ocurridas == 0


def test_cpu_con_tasa_uno_muta_cada_instruccion_copiada():
    cpu = CPU(GENOMA_ANCESTRAL, tasa_mutacion=1.0, rng=random.Random(1))
    cpu.run_hasta_replicar(max_pasos=200)
    assert cpu.replicacion_completa
    assert cpu.mutaciones_ocurridas == len(GENOMA_ANCESTRAL)


def test_tasa_empirica_converge_a_la_tasa_nominal():
    tasa_nominal = 0.0075
    rng = random.Random(123)
    total_mutaciones = 0
    total_copiadas = 0

    for _ in range(3000):
        cpu = CPU(GENOMA_ANCESTRAL, tasa_mutacion=tasa_nominal, rng=rng)
        cpu.run_hasta_replicar(max_pasos=200)
        total_mutaciones += cpu.mutaciones_ocurridas
        total_copiadas += cpu.write_head

    tasa_empirica = total_mutaciones / total_copiadas
    # Tolerancia amplia (±35% relativo) para que la prueba no sea frágil,
    # pero suficiente para detectar un error de cálculo real (ej. tasa
    # aplicada por replicación en vez de por instrucción).
    assert 0.0075 * 0.65 < tasa_empirica < 0.0075 * 1.35
