"""Pruebas de humo para la Fase 4, sub-fase 1.

Esto NO es todavía la estrategia de testing formal (esa se define en la
Fase 5, con pruebas de mutación, de selección y de regresión sobre
organismos ancestrales). Son verificaciones mínimas de que la CPU hace
lo que dice que hace, para poder avanzar con confianza a la sub-fase 2.
"""

from provida.vm.cpu import CPU, MASCARA_REGISTRO
from provida.vm.instructions import Instruccion as I


def test_mov_copia_el_valor_del_registro_origen():
    cpu = CPU([I("inc", ("BX",)), I("mov", ("AX", "BX"))])
    cpu.run(2)
    assert cpu.registros["AX"] == 1
    assert cpu.registros["BX"] == 1


def test_add_suma_registros():
    cpu = CPU([I("inc", ("AX",)), I("inc", ("BX",)), I("inc", ("BX",)), I("add", ("AX", "BX"))])
    cpu.run(4)
    assert cpu.registros["AX"] == 3  # 1 + 2


def test_nand_tabla_de_verdad_con_todos_los_bits_en_uno():
    # AX y BX en 0 -> NAND(0,0) debe dar todos los bits en 1 (el valor
    # máximo representable en 32 bits), no un número negativo de Python.
    cpu = CPU([I("nand", ("AX", "BX"))])
    cpu.run(1)
    assert cpu.registros["AX"] == MASCARA_REGISTRO


def test_push_pop_es_lifo():
    cpu = CPU([
        I("inc", ("AX",)),
        I("push", ("AX",)),
        I("inc", ("AX",)),
        I("push", ("AX",)),
        I("pop", ("BX",)),
    ])
    cpu.run(5)
    assert cpu.registros["BX"] == 2  # el último que entró (AX=2) es el primero en salir


def test_pop_de_pila_vacia_entrega_cero_sin_lanzar_excepcion():
    cpu = CPU([I("pop", ("AX",))])
    cpu.run(1)
    assert cpu.registros["AX"] == 0


def test_bucle_cuenta_atras_con_jmp_if_zero():
    genoma = [
        I("inc", ("BX",)),
        I("inc", ("BX",)),
        I("inc", ("BX",)),
        I("jmp-if-zero", ("BX", 4)),
        I("inc", ("AX",)),
        I("dec", ("BX",)),
        I("jmp", (-3,)),
        I("nop", ()),
    ]
    cpu = CPU(genoma)
    cpu.run(3 + 3 * 4 + 1)  # construir BX=3, tres iteraciones, chequeo final que sale
    assert cpu.registros["AX"] == 3
    assert cpu.registros["BX"] == 0


def test_genoma_es_circular():
    cpu = CPU([I("nop", ()), I("nop", ()), I("nop", ())])
    cpu.run(3)
    assert cpu.ip == 0  # tras 3 pasos sobre un genoma de 3 instrucciones, vuelve al inicio
