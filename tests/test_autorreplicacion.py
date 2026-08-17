"""Pruebas de humo para la Fase 4, sub-fase 2 (auto-replicación)."""

import pytest

from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I

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


def test_h_copy_sin_h_alloc_previo_lanza_error():
    cpu = CPU([I("h-copy", ())])
    with pytest.raises(RuntimeError):
        cpu.step()


def test_h_divide_con_copia_incompleta_no_completa_la_replicacion():
    # Genoma de 5 instrucciones, pero solo copiamos 2 antes de dividir.
    genoma = [I("h-alloc", ()), I("nop", ()), I("h-copy", ()), I("h-copy", ()), I("h-divide", ())]
    cpu = CPU(genoma)
    cpu.run(5)
    assert cpu.write_head == 2
    assert not cpu.replicacion_completa
    assert cpu.genoma_hijo == [genoma[0], genoma[1], None, None, None]


def test_organismo_ancestral_se_autorreplica_completo():
    cpu = CPU(GENOMA_ANCESTRAL)
    pasos = cpu.run_hasta_replicar(max_pasos=200)

    assert cpu.replicacion_completa
    assert pasos < 200  # terminó por sí mismo, no por agotar el límite de seguridad
    assert cpu.genoma_hijo == cpu.genoma
    assert cpu.write_head == len(GENOMA_ANCESTRAL)


def test_read_head_da_una_vuelta_completa_y_circular():
    cpu = CPU(GENOMA_ANCESTRAL)
    cpu.run_hasta_replicar(max_pasos=200)
    # Tras copiar las 13 instrucciones una por una desde la posición 0,
    # el read_head circular vuelve exactamente a 0.
    assert cpu.read_head == 0
