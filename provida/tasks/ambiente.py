import random

from provida.vm.instructions import ANCHO_REGISTRO_BITS


class Ambiente:
    """Fuente de inputs binarios para los organismos.

    Es deliberadamente mínimo (por ahora, solo genera bits al azar) --
    existe como clase separada, y no como una simple función, porque en
    la Fase 7 (extensiones) es el punto natural donde añadir recursos que
    se agotan por tarea o distribuciones de input no uniformes, sin tener
    que rediseñar cómo los organismos interactúan con "el mundo exterior".
    """

    def generar_input(self, rng: random.Random) -> int:
        return rng.getrandbits(ANCHO_REGISTRO_BITS)
