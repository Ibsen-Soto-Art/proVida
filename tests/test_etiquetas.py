"""Pruebas de la Fase 7: direccionamiento por contenido (nop-labels)."""

from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I

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


def test_leer_etiqueta_propia_se_detiene_en_instruccion_no_nop():
    genoma = [I("jmp-etiqueta", ()), I("nop-a", ()), I("nop-b", ()), I("h-divide", ())]
    cpu = CPU(genoma)
    assert cpu._leer_etiqueta_propia() == ["nop-a", "nop-b"]


def test_leer_etiqueta_propia_vacia_si_no_hay_nops_despues():
    genoma = [I("jmp-etiqueta", ()), I("h-divide", ())]
    cpu = CPU(genoma)
    assert cpu._leer_etiqueta_propia() == []


def test_buscar_complemento_encuentra_la_secuencia_complementaria():
    # nop-c en la posición 3 es el complemento de nop-b (A->B->C->A, ver
    # COMPLEMENTO_NOP: comp(nop-b) = nop-c).
    genoma = [I("jmp-etiqueta", ()), I("nop-b", ()), I("nop", ()), I("nop-c", ()), I("h-divide", ())]
    cpu = CPU(genoma)
    # etiqueta propia = ["nop-b"], complemento = ["nop-c"], debe encontrarlo en la posición 3
    destino = cpu._buscar_complemento(cpu._leer_etiqueta_propia())
    assert destino == 4  # justo después del nop-c encontrado


def test_buscar_complemento_sin_coincidencia_devuelve_none():
    genoma = [I("jmp-etiqueta", ()), I("nop-a", ()), I("h-divide", ())]
    cpu = CPU(genoma)
    assert cpu._buscar_complemento(cpu._leer_etiqueta_propia()) is None


def test_jmp_etiqueta_sin_complemento_no_hace_nada():
    genoma = [I("jmp-etiqueta", ()), I("nop-a", ()), I("h-divide", ())]
    cpu = CPU(genoma)
    cpu.step()
    assert cpu.ip == 1  # avanzó normalmente, no crasheó


def test_jmp_etiqueta_salta_al_complemento():
    genoma = [I("jmp-etiqueta", ()), I("nop-b", ()), I("nop", ()), I("nop-c", ()), I("h-divide", ())]
    cpu = CPU(genoma)
    cpu.step()
    assert cpu.ip == 4  # justo después del nop-c en la posición 3


def test_jmp_cero_etiqueta_solo_salta_si_el_registro_es_cero():
    genoma = [
        I("jmp-cero-etiqueta", ("AX",)),
        I("nop-b", ()),
        I("nop", ()),
        I("nop-c", ()),
        I("h-divide", ()),
    ]
    cpu = CPU(genoma)
    cpu.registros["AX"] = 1
    cpu.step()
    assert cpu.ip == 1  # AX != 0: no salta

    cpu2 = CPU(genoma)
    cpu2.step()  # AX empieza en 0
    assert cpu2.ip == 4  # salta al complemento


def test_organismo_ancestral_por_etiquetas_se_autorreplica_sin_conocer_su_tamano():
    cpu = CPU(GENOMA_ANCESTRAL_POR_ETIQUETAS)
    pasos = cpu.run_hasta_replicar(max_pasos=300)

    assert cpu.replicacion_completa
    assert pasos < 300
    assert cpu.genoma_hijo == GENOMA_ANCESTRAL_POR_ETIQUETAS


def test_mutacion_que_rompe_una_etiqueta_no_crashea_solo_falla_en_saltar():
    # Sustituimos a mano el nop-a de la posición 4 (etiqueta propia de
    # jmp-vuelta-etiqueta) por algo que no es un nop de etiqueta --
    # simula lo que una mutación real podría hacer.
    genoma_roto = list(GENOMA_ANCESTRAL_POR_ETIQUETAS)
    genoma_roto[4] = I("inc", ("AX",))
    cpu = CPU(genoma_roto)
    cpu.run(50)  # no debe lanzar ninguna excepción
    assert cpu.instrucciones_ejecutadas == 50
