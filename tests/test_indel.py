"""Pruebas de la Fase 7: mutación por inserción/deleción (indels)."""

import random

from provida.mutation.sustitucion import procesar_copia
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


def test_sin_insercion_ni_delecion_procesar_copia_es_igual_a_copiar_con_mutacion():
    # Verifica el "camino rápido": con ambas tasas en 0, el resultado (y
    # el consumo del generador aleatorio) debe ser idéntico al de
    # copiar_con_mutacion -- esto es lo que protege las pruebas de
    # regresión de la Fase 5.
    original = I("inc", ("AX",))
    rng_a = random.Random(5)
    rng_b = random.Random(5)

    instrucciones, tipo = procesar_copia(original, 0.3, 10, rng_a)
    from provida.mutation.sustitucion import copiar_con_mutacion

    esperado, hubo_mutacion = copiar_con_mutacion(original, 0.3, 10, rng_b)

    assert instrucciones == [esperado]
    assert tipo == ("sustitucion" if hubo_mutacion else None)
    assert rng_a.random() == rng_b.random()  # el generador quedó en el mismo estado


def test_insercion_produce_dos_instrucciones():
    rng = random.Random(1)
    original = I("inc", ("AX",))
    instrucciones, tipo = procesar_copia(original, 0.0, 10, rng, tasa_insercion=1.0)
    assert tipo == "insercion"
    assert len(instrucciones) == 2
    assert instrucciones[0] == original


def test_delecion_no_produce_ninguna_instruccion():
    rng = random.Random(1)
    original = I("inc", ("AX",))
    instrucciones, tipo = procesar_copia(original, 0.0, 10, rng, tasa_delecion=1.0)
    assert tipo == "delecion"
    assert instrucciones == []


def test_cpu_con_insercion_activa_la_cria_crece():
    cpu = CPU(
        GENOMA_ANCESTRAL_POR_ETIQUETAS,
        tasa_insercion=1.0,
        rng=random.Random(2),
    )
    cpu.run_hasta_replicar(max_pasos=300)
    assert cpu.replicacion_completa
    assert len(cpu.genoma_hijo) > len(GENOMA_ANCESTRAL_POR_ETIQUETAS)
    assert cpu.mutaciones_insercion == len(GENOMA_ANCESTRAL_POR_ETIQUETAS)


def test_cpu_con_delecion_activa_la_cria_encoge():
    # Con tasa_delecion=1.0 la cría nunca dejaría de estar vacía (cada
    # h-copy borra lo que iba a escribir), y jmp-vuelta-etiqueta exige una
    # cría NO vacía para poder disparar -- así que el organismo jamás
    # detectaría "vuelta completa" y nunca llegaría a dividirse. Una tasa
    # más moderada permite que, en promedio, algo sí quede escrito.
    cpu = CPU(
        GENOMA_ANCESTRAL_POR_ETIQUETAS,
        tasa_delecion=0.3,
        rng=random.Random(2),
    )
    cpu.run_hasta_replicar(max_pasos=2000)
    assert cpu.replicacion_completa
    assert len(cpu.genoma_hijo) < len(GENOMA_ANCESTRAL_POR_ETIQUETAS)
    assert cpu.mutaciones_delecion > 0


def test_tope_de_crecimiento_evita_un_genoma_infinito():
    # Un bucle de puro h-copy, sin ninguna condición de salida, copiaría
    # para siempre sin el tope de seguridad. h-alloc no está dentro del
    # bucle (lo ejecutamos una sola vez a mano) para que no reinicie la
    # cría en cada vuelta.
    genoma_solo_copia = [I("h-copy", ())]
    cpu = CPU(genoma_solo_copia, rng=random.Random(0))
    cpu.genoma_hijo = []  # equivalente a haber ejecutado h-alloc una vez
    cpu.run(500)
    assert len(cpu.genoma_hijo) == 4 * len(genoma_solo_copia)  # LONGITUD_MAXIMA_HIJO_RELATIVA
