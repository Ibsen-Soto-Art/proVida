import random

from provida.tasks.temperatura import ANCHO_TOLERANCIA_POR_DEFECTO
from provida.vm.instructions import ANCHO_REGISTRO_BITS


class Ambiente:
    """Fuente de inputs binarios para los organismos, y calendario de
    temperatura del mundo.

    Es deliberadamente mínimo -- existe como clase separada, y no como
    una simple función, porque es el punto natural donde añadir más
    condiciones ambientales (recursos que se agotan, temperatura, lo que
    siga) sin tener que rediseñar cómo los organismos interactúan con
    "el mundo exterior".

    La temperatura sigue una rampa lineal: `temperatura_inicial +
    tasa_cambio_temperatura * turno`. Con `tasa_cambio_temperatura=0.0`
    (el valor por defecto) la temperatura es constante -- y, como además
    `temperatura_optima` empieza en None para todo organismo que nunca
    ejecute `set-temperatura`, un Ambiente() sin argumentos se comporta
    exactamente igual que antes de esta extensión.
    """

    def __init__(
        self,
        temperatura_inicial: float = 20.0,
        tasa_cambio_temperatura: float = 0.0,
        ancho_tolerancia: float = ANCHO_TOLERANCIA_POR_DEFECTO,
    ):
        self.temperatura_inicial = temperatura_inicial
        self.tasa_cambio_temperatura = tasa_cambio_temperatura
        self.ancho_tolerancia = ancho_tolerancia

    def generar_input(self, rng: random.Random) -> int:
        return rng.getrandbits(ANCHO_REGISTRO_BITS)

    def temperatura_en(self, turno: int) -> float:
        return self.temperatura_inicial + self.tasa_cambio_temperatura * turno
