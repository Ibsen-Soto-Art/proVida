"""Pruebas de la extensión de temperatura (post-Fase 8): presión de
selección por un óptimo ambiental que se mueve con el tiempo.
"""

import math
import random

from provida.tasks.ambiente import Ambiente
from provida.tasks.temperatura import factor_temperatura, valor_a_temperatura
from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I
from provida.world.grid import Mundo


def test_factor_temperatura_es_1_si_no_hay_preferencia_declarada():
    assert factor_temperatura(None, temperatura_actual=20.0) == 1.0


def test_factor_temperatura_es_1_cuando_coincide_exactamente():
    assert factor_temperatura(20.0, temperatura_actual=20.0) == 1.0


def test_factor_temperatura_decae_de_forma_simetrica_y_monotona():
    f_cerca = factor_temperatura(20.0, temperatura_actual=22.0)
    f_lejos = factor_temperatura(20.0, temperatura_actual=40.0)
    f_muy_lejos = factor_temperatura(20.0, temperatura_actual=100.0)

    assert 0.0 < f_muy_lejos < f_lejos < f_cerca < 1.0
    # Simétrico: da igual si el ambiente está más frío o más caliente que
    # el óptimo, mientras la distancia sea la misma.
    assert factor_temperatura(20.0, 25.0) == factor_temperatura(20.0, 15.0)


def test_factor_temperatura_nunca_llega_exactamente_a_cero():
    # Gradiente suave (decisión de diseño): incluso bastante lejos del
    # óptimo, sigue habiendo una probabilidad (pequeñísima) de ser
    # elegido -- una diferencia extrema (ej. 1000 grados) sí puede
    # subdesbordar a 0.0 en punto flotante, lo cual es una limitación
    # numérica esperada, no una violación del diseño.
    f = factor_temperatura(20.0, temperatura_actual=120.0)
    assert f > 0.0


def test_valor_a_temperatura_cae_dentro_del_rango_esperado():
    for valor in [0, 1, 50, 99, 100, 4_294_967_295, 12345]:
        temperatura = valor_a_temperatura(valor)
        assert -50.0 <= temperatura < 50.0


def test_ambiente_temperatura_constante_por_defecto():
    ambiente = Ambiente(temperatura_inicial=15.0)
    assert ambiente.temperatura_en(0) == 15.0
    assert ambiente.temperatura_en(10_000) == 15.0


def test_ambiente_rampa_lineal():
    ambiente = Ambiente(temperatura_inicial=10.0, tasa_cambio_temperatura=0.001)
    assert ambiente.temperatura_en(0) == 10.0
    assert ambiente.temperatura_en(1000) == 11.0
    assert ambiente.temperatura_en(2000) == 12.0


def test_instruccion_set_temperatura_no_necesita_ambiente():
    cpu = CPU([I("set-temperatura", ("AX",))])
    assert cpu.temperatura_optima is None
    cpu.step()
    assert cpu.temperatura_optima is not None  # es un rasgo del organismo, no del ambiente


def test_instruccion_set_temperatura_usa_el_valor_del_registro():
    cpu = CPU([I("inc", ("AX",)), I("set-temperatura", ("AX",))])
    cpu.run(2)
    assert cpu.temperatura_optima == valor_a_temperatura(1)


def test_peso_efectivo_sin_ambiente_es_igual_al_merit():
    mundo = Mundo(3, 3, rng=random.Random(0))
    cpu = CPU([I("nop", ())], merit=5.0)  # sin ambiente
    assert mundo._peso_efectivo(cpu) == 5.0


def test_peso_efectivo_con_ambiente_pero_sin_temperatura_declarada_es_igual_al_merit():
    mundo = Mundo(3, 3, rng=random.Random(0))
    cpu = CPU([I("nop", ())], merit=5.0, ambiente=Ambiente())
    assert mundo._peso_efectivo(cpu) == 5.0  # temperatura_optima sigue en None


def test_peso_efectivo_penaliza_desajuste_de_temperatura():
    ambiente = Ambiente(temperatura_inicial=20.0)
    mundo = Mundo(3, 3, rng=random.Random(0))
    bien_adaptado = CPU([I("nop", ())], merit=1.0, ambiente=ambiente, temperatura_optima=20.0)
    mal_adaptado = CPU([I("nop", ())], merit=1.0, ambiente=ambiente, temperatura_optima=80.0)

    assert mundo._peso_efectivo(bien_adaptado) == 1.0
    assert mundo._peso_efectivo(mal_adaptado) < mundo._peso_efectivo(bien_adaptado)


def test_scheduling_favorece_al_organismo_mejor_adaptado_a_la_temperatura_actual():
    # Dos organismos que nunca se replican (un solo nop), mismo merit
    # base, pero uno coincide con la temperatura del ambiente y el otro
    # no. Sobre muchos turnos, el mejor adaptado debe ser elegido muchas
    # más veces -- el mismo patrón que ya probamos para merit por tareas.
    ambiente = Ambiente(temperatura_inicial=20.0)
    mundo = Mundo(3, 3, rng=random.Random(5))
    bien_adaptado = CPU([I("nop", ())], merit=1.0, ambiente=ambiente, temperatura_optima=20.0)
    mal_adaptado = CPU([I("nop", ())], merit=1.0, ambiente=ambiente, temperatura_optima=90.0)
    mundo.colocar(bien_adaptado, 0, 0)
    mundo.colocar(mal_adaptado, 0, 1)

    mundo.ejecutar_ciclos(2000, instrucciones_por_turno=1)

    assert bien_adaptado.instrucciones_ejecutadas > 5 * mal_adaptado.instrucciones_ejecutadas


def test_cria_hereda_la_temperatura_optima_del_padre():
    genoma = [
        I("h-alloc", ()),               # 0
        I("inc", ("AX",)),              # 1
        I("set-temperatura", ("AX",)),  # 2
        I("inc", ("CX",)),              # 3   CX=1
        I("add", ("CX", "CX")),         # 4   CX=2
        I("inc", ("CX",)),              # 5   CX=3
        I("add", ("CX", "CX")),         # 6   CX=6
        I("inc", ("CX",)),              # 7   CX=7
        I("add", ("CX", "CX")),         # 8   CX=14
        I("inc", ("CX",)),              # 9   CX=15 = len(genoma)
        I("jmp-if-zero", ("CX", 4)),    # 10
        I("h-copy", ()),                # 11
        I("dec", ("CX",)),              # 12
        I("jmp", (-3,)),                # 13
        I("h-divide", ()),              # 14
    ]
    assert len(genoma) == 15
    rng = random.Random(3)
    mundo = Mundo(5, 5, rng=rng)
    padre = CPU(genoma, rng=rng, ambiente=Ambiente())
    mundo.colocar(padre, 2, 2)

    turnos = 0
    while mundo.nacimientos < 1 and turnos < 2000:
        mundo.ejecutar_ciclo(instrucciones_por_turno=1)
        turnos += 1

    assert mundo.nacimientos == 1
    assert padre.temperatura_optima is not None
    hijo = next(cpu for f, c, cpu in mundo.organismos_vivos() if (f, c) != (2, 2))
    assert hijo.temperatura_optima == padre.temperatura_optima
