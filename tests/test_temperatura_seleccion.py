"""Prueba de integración de la extensión de temperatura: un ambiente que
se calienta invierte cuál de dos genotipos (misma longitud, distinta
temperatura óptima) domina la población -- y un control sin calentamiento
confirma que la inversión es real, no un artefacto. Mismo experimento y
parámetros que examples/demo_temperatura.py.
"""

import random

from provida.tasks.ambiente import Ambiente
from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I
from provida.world.grid import Mundo


def _construir_valor(registro: str, objetivo: int) -> list[I]:
    bits = bin(objetivo)[2:]
    instrucciones = [I("inc", (registro,))]
    for bit in bits[1:]:
        instrucciones.append(I("add", (registro, registro)))
        if bit == "1":
            instrucciones.append(I("inc", (registro,)))
    return instrucciones


OBJETIVOS = {"frio": 35, "calido": 65}  # -> -15.0°C y +15.0°C
SEGMENTOS = {nombre: _construir_valor("AX", v) for nombre, v in OBJETIVOS.items()}
LONGITUD_MAXIMA_SEGMENTO = max(len(s) for s in SEGMENTOS.values())


def _genoma_para(nombre: str) -> list[I]:
    construccion = SEGMENTOS[nombre]
    relleno = [I("nop", ())] * (LONGITUD_MAXIMA_SEGMENTO - len(construccion))
    return (
        [I("h-alloc", ())]
        + construccion + relleno
        + [I("set-temperatura", ("AX",))]
        + [I("nop-a", ()), I("h-copy", ()), I("jmp-vuelta-etiqueta", ()), I("nop-a", ()),
           I("jmp-etiqueta", ()), I("nop-c", ()), I("nop", ()), I("nop-b", ()), I("h-divide", ())]
    )


GENOMAS = {nombre: _genoma_para(nombre) for nombre in OBJETIVOS}
POSICIONES_FRIO = [(2, 2), (2, 12), (12, 2), (12, 12)]
POSICIONES_CALIDO = [(7, 3), (3, 7), (11, 7), (7, 11)]


def _correr(tasa_cambio_temperatura: float, turnos: int) -> tuple[int, int, int]:
    rng = random.Random(11)
    ambiente = Ambiente(temperatura_inicial=-15.0, tasa_cambio_temperatura=tasa_cambio_temperatura)
    mundo = Mundo(ancho=15, alto=15, rng=rng)
    for fila, columna in POSICIONES_FRIO:
        mundo.colocar(CPU(GENOMAS["frio"], tasa_mutacion=0.0075, rng=rng, ambiente=ambiente), fila, columna)
    for fila, columna in POSICIONES_CALIDO:
        mundo.colocar(CPU(GENOMAS["calido"], tasa_mutacion=0.0075, rng=rng, ambiente=ambiente), fila, columna)
    mundo.ejecutar_ciclos(turnos, instrucciones_por_turno=3)

    vivos = mundo.organismos_vivos()
    frios = sum(1 for _, _, cpu in vivos if cpu.temperatura_optima is not None and cpu.temperatura_optima < 0)
    calidos = sum(1 for _, _, cpu in vivos if cpu.temperatura_optima is not None and cpu.temperatura_optima >= 0)
    return len(vivos), frios, calidos


def test_genomas_frio_y_calido_tienen_la_misma_longitud():
    assert len(GENOMAS["frio"]) == len(GENOMAS["calido"])


def test_calentamiento_invierte_la_dominancia_hacia_el_genotipo_calido():
    # Tasa de calentamiento más alta que en el demo (0.0005 vs 0.0003) y
    # menos turnos (100k vs 160k) -- solo para que la suite de pruebas
    # siga corriendo en segundos y no en medio minuto; el fenómeno es el
    # mismo, observado en la práctica: 191/225 (~85%) para el cálido.
    poblacion, _, calidos = _correr(tasa_cambio_temperatura=0.0005, turnos=100_000)
    assert calidos / poblacion > 0.8


def test_control_sin_calentamiento_el_frio_nunca_pierde_su_ventaja():
    poblacion, frios, _ = _correr(tasa_cambio_temperatura=0.0, turnos=100_000)
    # Mismo experimento, temperatura constante en -15°C (favorece al
    # frío desde el principio y para siempre). Si esto también mostrara
    # una inversión hacia el cálido, la del test anterior no se podría
    # atribuir al calentamiento.
    assert frios / poblacion > 0.9
