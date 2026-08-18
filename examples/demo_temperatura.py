"""Demo de la extensión de temperatura: selección por un óptimo ambiental
que se mueve con el tiempo (el mismo fenómeno detrás de la adaptación al
cambio climático en biología real).

Dos genotipos, de la MISMA longitud (el único punto en que difieren es su
temperatura óptima -- 19 instrucciones cada uno, la única diferencia es
qué valor construyen en AX antes de `set-temperatura`):

  - "frío": declara -15°C como su óptimo.
  - "cálido": declara +15°C como su óptimo.

El ambiente empieza en -15°C (favoreciendo al frío) y se calienta
gradualmente hasta superar los +15°C. Ninguna línea de código decide
"ahora debe ganar el cálido" -- es una consecuencia de que el
planificador pondera el merit por qué tan bien encaja la temperatura
declarada con la temperatura actual (ver provida/world/grid.py,
`_peso_efectivo`), recalculada en cada turno.

Nota de diseño: la "sucesión" que se observa aquí viene de que YA HABÍA
dos genotipos distintos compitiendo desde el principio (variación
genética preexistente) -- no de que un solo linaje mute gradualmente su
preferencia sobre la marcha. Esa distinción (adaptación desde variación
preexistente vs. desde mutación nueva) es real en biología evolutiva:
la primera responde mucho más rápido a un cambio ambiental que la
segunda, y aquí se puede ver por qué.
"""

import random

from provida.tasks.ambiente import Ambiente
from provida.tasks.temperatura import valor_a_temperatura
from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I
from provida.world.grid import Mundo


def construir_valor(registro: str, objetivo: int) -> list[I]:
    """Genera instrucciones que construyen `objetivo` en `registro` usando
    inc + duplicación binaria (~log2(objetivo) instrucciones en vez de
    `objetivo` instrucciones de puro `inc`)."""
    bits = bin(objetivo)[2:]
    instrucciones = [I("inc", (registro,))]
    for bit in bits[1:]:
        instrucciones.append(I("add", (registro, registro)))
        if bit == "1":
            instrucciones.append(I("inc", (registro,)))
    return instrucciones


OBJETIVOS = {"frio": 35, "calido": 65}  # -> -15.0°C y +15.0°C (ver valor_a_temperatura)
SEGMENTOS = {nombre: construir_valor("AX", v) for nombre, v in OBJETIVOS.items()}
LONGITUD_MAXIMA_SEGMENTO = max(len(s) for s in SEGMENTOS.values())


def genoma_para(nombre: str) -> list[I]:
    construccion = SEGMENTOS[nombre]
    relleno = [I("nop", ())] * (LONGITUD_MAXIMA_SEGMENTO - len(construccion))
    # Genoma ancestral por etiquetas (Fase 7): no necesita contar sus
    # propias instrucciones, así que el segmento de construcción de AX
    # puede tener cualquier longitud (con relleno para igualar entre
    # genotipos) sin tener que recalcular ningún offset numérico.
    return (
        [I("h-alloc", ())]
        + construccion + relleno
        + [I("set-temperatura", ("AX",))]
        + [I("nop-a", ()), I("h-copy", ()), I("jmp-vuelta-etiqueta", ()), I("nop-a", ()),
           I("jmp-etiqueta", ()), I("nop-c", ()), I("nop", ()), I("nop-b", ()), I("h-divide", ())]
    )


GENOMAS = {nombre: genoma_para(nombre) for nombre in OBJETIVOS}
assert len(GENOMAS["frio"]) == len(GENOMAS["calido"]), "misma longitud: la única ventaja debe venir de la temperatura"

POSICIONES_FRIO = [(2, 2), (2, 12), (12, 2), (12, 12)]
POSICIONES_CALIDO = [(7, 3), (3, 7), (11, 7), (7, 11)]


def correr_experimento(tasa_cambio_temperatura: float, turnos: int) -> tuple[int, int, int]:
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


print(f"Temperatura óptima 'frío': {valor_a_temperatura(OBJETIVOS['frio'])}°C")
print(f"Temperatura óptima 'cálido': {valor_a_temperatura(OBJETIVOS['calido'])}°C")

print("\n=== Experimento: ambiente calentándose (-15°C -> ~+33°C en 160k turnos) ===")
poblacion, frios, calidos = correr_experimento(tasa_cambio_temperatura=0.0003, turnos=160_000)
print(f"Turno 160000: población={poblacion}  fríos={frios}  cálidos={calidos}")
assert calidos / poblacion > 0.8, "el genotipo cálido debería haber desplazado al frío"

print("\n=== Control: mismo experimento, SIN calentamiento (temperatura constante en -15°C) ===")
poblacion_ctrl, frios_ctrl, calidos_ctrl = correr_experimento(tasa_cambio_temperatura=0.0, turnos=160_000)
print(f"Turno 160000: población={poblacion_ctrl}  fríos={frios_ctrl}  cálidos={calidos_ctrl}")
assert frios_ctrl / poblacion_ctrl > 0.9, "sin calentamiento, el frío debería seguir dominando"

print(
    "\nCon calentamiento, la dominancia se invierte (el cálido termina ganando). "
    "Sin calentamiento (control), el frío nunca pierde su ventaja inicial. "
    "La diferencia entre ambas corridas es la prueba de que el efecto es real "
    "y no un artefacto del experimento."
)
