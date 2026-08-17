"""Pruebas de humo para la Fase 6 (metadatos de linaje y registro de eventos)."""

import random

from provida.metrics.registro import RegistroEventos
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


def test_colocar_asigna_id_automaticamente():
    mundo = Mundo(3, 3, rng=random.Random(0))
    cpu = CPU(GENOMA_ANCESTRAL)
    assert cpu.id_organismo is None
    mundo.colocar(cpu, 0, 0)
    assert cpu.id_organismo == 0

    otro = CPU(GENOMA_ANCESTRAL)
    mundo.colocar(otro, 0, 1)
    assert otro.id_organismo == 1


def test_cria_hereda_generacion_y_referencia_al_padre():
    mundo = Mundo(5, 5, rng=random.Random(1))
    padre = CPU(GENOMA_ANCESTRAL, rng=mundo.rng)
    mundo.colocar(padre, 2, 2)
    assert padre.generacion == 0

    turnos = 0
    while mundo.nacimientos < 1 and turnos < 1000:
        mundo.ejecutar_ciclo()
        turnos += 1

    hijo = next(cpu for f, c, cpu in mundo.organismos_vivos() if (f, c) != (2, 2))
    assert hijo.generacion == 1
    assert hijo.id_padre == padre.id_organismo
    assert hijo.id_organismo != padre.id_organismo


def test_mundo_sin_registro_no_falla_al_nacer():
    mundo = Mundo(5, 5, rng=random.Random(1))  # registro=None por defecto
    mundo.colocar(CPU(GENOMA_ANCESTRAL, rng=mundo.rng), 2, 2)
    mundo.ejecutar_ciclos(1000)  # no debe lanzar excepción
    assert mundo.nacimientos >= 1


def test_registro_de_eventos_captura_el_nacimiento():
    registro = RegistroEventos()
    mundo = Mundo(5, 5, rng=random.Random(1), registro=registro)
    padre = CPU(GENOMA_ANCESTRAL, rng=mundo.rng)
    mundo.colocar(padre, 2, 2)

    turnos = 0
    while mundo.nacimientos < 1 and turnos < 1000:
        mundo.ejecutar_ciclo()
        turnos += 1

    assert len(registro.nacimientos) == 1
    evento = registro.nacimientos[0]
    assert evento["id_padre"] == padre.id_organismo
    assert evento["generacion"] == 1
    assert evento["turno"] == mundo.turno


def test_registro_de_snapshot_calcula_merit_promedio_y_conteo_de_tareas():
    registro = RegistroEventos()
    mundo = Mundo(3, 3, rng=random.Random(0))

    debil = CPU(GENOMA_ANCESTRAL, merit=1.0)
    fuerte = CPU(GENOMA_ANCESTRAL, merit=3.0)
    fuerte.tareas_resueltas = {"NAND"}
    mundo.colocar(debil, 0, 0)
    mundo.colocar(fuerte, 0, 1)

    registro.registrar_snapshot(turno=42, mundo=mundo)

    assert len(registro.snapshots) == 1
    snap = registro.snapshots[0]
    assert snap["turno"] == 42
    assert snap["poblacion"] == 2
    assert snap["merit_promedio"] == 2.0  # (1.0 + 3.0) / 2
    assert snap["conteo_tareas"] == {"NAND": 1}


def test_registro_de_snapshot_con_mundo_vacio_no_falla():
    registro = RegistroEventos()
    mundo = Mundo(2, 2, rng=random.Random(0))
    registro.registrar_snapshot(turno=0, mundo=mundo)
    assert registro.snapshots[0]["merit_promedio"] == 0.0
