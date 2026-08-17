"""Pruebas de humo para la Fase 4, sub-fase 2 (auto-replicación)."""

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


def test_h_copy_sin_h_alloc_previo_no_hace_nada_ni_falla():
    # Revisado en la sub-fase 4: en una población, un genoma "torpe" (de
    # fábrica o mutado) no debe poder crashear la simulación entera. Antes
    # esto lanzaba RuntimeError; ahora es simplemente un no-op.
    cpu = CPU([I("h-copy", ())])
    cpu.step()  # no debe lanzar excepción
    assert cpu.genoma_hijo is None
    assert cpu.ip == 0  # genoma de una sola instrucción, circular


def test_h_divide_con_copia_incompleta_completa_con_una_cria_truncada():
    # Revisado en la Fase 7: con genoma_hijo como lista creciente (para
    # soportar inserción/deleción), ya no existe un "tamaño objetivo"
    # contra el cual comparar -- h-divide confía en que el organismo
    # decidió copiar lo suficiente (igual que Avida real). Un h-divide
    # prematuro SÍ completa, pero con una cría más corta y distinta al
    # padre -- una cría defectuosa, no un error de la CPU.
    genoma = [I("h-alloc", ()), I("nop", ()), I("h-copy", ()), I("h-copy", ()), I("h-divide", ())]
    cpu = CPU(genoma)
    cpu.run(5)
    assert cpu.write_head == 2
    assert cpu.replicacion_completa
    assert cpu.genoma_hijo == [genoma[0], genoma[1]]
    assert cpu.genoma_hijo != genoma  # la cría quedó truncada, no es una copia completa


def test_h_divide_sin_haber_copiado_nada_no_completa():
    genoma = [I("h-alloc", ()), I("h-divide", ())]
    cpu = CPU(genoma)
    cpu.run(2)
    assert not cpu.replicacion_completa
    assert cpu.genoma_hijo == []


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
