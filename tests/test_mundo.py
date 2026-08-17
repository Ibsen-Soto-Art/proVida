"""Pruebas de humo para la Fase 4, sub-fase 4 (población / mundo espacial)."""

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


def test_mundo_vacio_no_hace_nada_al_ejecutar_un_ciclo():
    mundo = Mundo(3, 3, rng=random.Random(0))
    mundo.ejecutar_ciclo()  # no debe lanzar excepción con la rejilla vacía
    assert mundo.poblacion_actual() == 0


def _ejecutar_hasta_el_primer_nacimiento(mundo: Mundo, max_turnos: int = 1000) -> None:
    # No usamos un número fijo de turnos: con un solo organismo vivo, TODOS
    # los turnos van a parar a él (nadie más con quien competir), así que
    # completa su replicación mucho más rápido que en una población ya
    # crecida. Paramos justo en el primer nacimiento para que la prueba no
    # dependa de cuántas replicaciones adicionales alcancen a ocurrir después.
    turnos = 0
    while mundo.nacimientos < 1 and turnos < max_turnos:
        mundo.ejecutar_ciclo(instrucciones_por_turno=1)
        turnos += 1
    assert mundo.nacimientos == 1, "no hubo nacimiento dentro del límite de turnos de la prueba"


def test_un_organismo_se_replica_y_la_poblacion_crece_a_dos():
    mundo = Mundo(5, 5, rng=random.Random(1))
    mundo.colocar(CPU(GENOMA_ANCESTRAL, rng=mundo.rng), fila=2, columna=2)
    _ejecutar_hasta_el_primer_nacimiento(mundo)
    assert mundo.poblacion_actual() == 2
    assert mundo.nacimientos == 1


def test_la_cria_nace_en_el_vecindario_de_moore_del_padre():
    mundo = Mundo(5, 5, rng=random.Random(1))
    mundo.colocar(CPU(GENOMA_ANCESTRAL, rng=mundo.rng), fila=2, columna=2)
    _ejecutar_hasta_el_primer_nacimiento(mundo)

    posiciones_ocupadas = [(f, c) for f, c, _ in mundo.organismos_vivos()]
    assert (2, 2) in posiciones_ocupadas  # el padre sigue vivo, renacido
    otras = [p for p in posiciones_ocupadas if p != (2, 2)]
    assert len(otras) == 1
    f_hijo, c_hijo = otras[0]
    # Distancia de tablero de ajedrez (Chebyshev) 1 = vecino directo,
    # considerando el envolvimiento toroidal en una rejilla de 5x5.
    df = min(abs(f_hijo - 2), 5 - abs(f_hijo - 2))
    dc = min(abs(c_hijo - 2), 5 - abs(c_hijo - 2))
    assert max(df, dc) == 1


def test_la_cria_hereda_el_genoma_del_padre_sin_mutacion():
    mundo = Mundo(5, 5, rng=random.Random(1))
    mundo.colocar(CPU(GENOMA_ANCESTRAL, rng=mundo.rng), fila=2, columna=2)
    _ejecutar_hasta_el_primer_nacimiento(mundo)

    genomas = [cpu.genoma for _, _, cpu in mundo.organismos_vivos()]
    assert all(g == GENOMA_ANCESTRAL for g in genomas)


def test_padre_renace_con_estado_limpio_tras_dividir():
    mundo = Mundo(5, 5, rng=random.Random(1))
    padre = CPU(GENOMA_ANCESTRAL, rng=mundo.rng)
    mundo.colocar(padre, fila=2, columna=2)
    _ejecutar_hasta_el_primer_nacimiento(mundo)

    assert padre.ip == 0
    assert padre.read_head == 0
    assert padre.write_head == 0
    assert padre.genoma_hijo is None
    assert not padre.replicacion_completa


def test_poblacion_llena_la_rejilla_y_luego_hay_reemplazos():
    mundo = Mundo(4, 4, rng=random.Random(3))
    mundo.colocar(CPU(GENOMA_ANCESTRAL, rng=mundo.rng), fila=1, columna=1)
    mundo.ejecutar_ciclos(3000, instrucciones_por_turno=2)

    assert mundo.poblacion_actual() == 16
    assert mundo.nacimientos > 16  # más nacimientos que espacio: hubo recambio
    assert mundo.reemplazos > 0


def test_scheduling_ponderado_por_merit_favorece_al_de_mayor_merit():
    # Dos organismos que NUNCA se replican (genoma de un solo nop), uno
    # con merit 10x el otro. Tras muchos turnos, el de mayor merit debe
    # haber sido elegido muchas más veces (medido por instrucciones
    # ejecutadas, ya que cada elección ejecuta una instrucción).
    mundo = Mundo(3, 3, rng=random.Random(5))
    debil = CPU([I("nop", ())], merit=1.0)
    fuerte = CPU([I("nop", ())], merit=10.0)
    mundo.colocar(debil, 0, 0)
    mundo.colocar(fuerte, 0, 1)

    mundo.ejecutar_ciclos(2000, instrucciones_por_turno=1)

    assert fuerte.instrucciones_ejecutadas > 5 * debil.instrucciones_ejecutadas
