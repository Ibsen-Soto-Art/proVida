import random

from provida.vm.instructions import ARIDAD_OPCODES, Instruccion

REGISTROS = ("AX", "BX", "CX")

# Valor clásico usado en los experimentos de Avida: 0.75% de probabilidad
# de mutación por cada instrucción copiada durante la auto-replicación.
TASA_MUTACION_POR_DEFECTO = 0.0075


def instruccion_aleatoria(rng: random.Random, longitud_genoma: int) -> Instruccion:
    """Genera una instrucción válida al azar, uniforme sobre todo el set de opcodes.

    Uniforme sobre opcodes (no sobre instrucciones individuales) porque no
    hay ninguna razón biológica o de diseño para que unos opcodes sean más
    "probables" que otros como resultado de una mutación -- cualquier
    instrucción del set es un destino igual de válido.
    """
    opcode = rng.choice(list(ARIDAD_OPCODES))
    aridad = ARIDAD_OPCODES[opcode]

    if opcode == "jmp":
        return Instruccion(opcode, (rng.randint(-longitud_genoma, longitud_genoma),))
    if opcode == "jmp-if-zero":
        offset = rng.randint(-longitud_genoma, longitud_genoma)
        return Instruccion(opcode, (rng.choice(REGISTROS), offset))
    if aridad == 0:
        return Instruccion(opcode, ())
    # El resto de opcodes con operandos (mov, inc, dec, add, nand, push, pop)
    # solo toman registros como argumentos.
    return Instruccion(opcode, tuple(rng.choice(REGISTROS) for _ in range(aridad)))


def copiar_con_mutacion(
    instruccion: Instruccion,
    tasa_mutacion: float,
    longitud_genoma: int,
    rng: random.Random,
) -> tuple[Instruccion, bool]:
    """Decide qué instrucción escribir en la cría al copiar una del padre.

    Devuelve (instrucción_a_escribir, hubo_intento_de_mutación). El segundo
    valor existe por separado de "la instrucción cambió" porque una mutación
    puede, por azar, regenerar la misma instrucción original -- igual que
    una mutación silenciosa en un codón. Para medir la tasa de mutación
    empírica hace falta contar los intentos, no solo los cambios visibles.
    """
    if rng.random() < tasa_mutacion:
        return instruccion_aleatoria(rng, longitud_genoma), True
    return instruccion, False
