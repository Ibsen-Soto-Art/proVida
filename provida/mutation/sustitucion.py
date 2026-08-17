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


def procesar_copia(
    instruccion: Instruccion,
    tasa_sustitucion: float,
    longitud_genoma: int,
    rng: random.Random,
    tasa_insercion: float = 0.0,
    tasa_delecion: float = 0.0,
) -> tuple[list[Instruccion], str | None]:
    """Como `copiar_con_mutacion`, pero además puede insertar o eliminar
    instrucciones -- lo que permite que el genoma de la cría cambie de
    tamaño (Fase 7). Devuelve (instrucciones_a_escribir, tipo_de_evento),
    donde `tipo_de_evento` es None, "sustitucion", "insercion" o "delecion".

    Con tasa_insercion=tasa_delecion=0.0 (el valor por defecto), esta
    función consume el generador aleatorio EXACTAMENTE igual que
    `copiar_con_mutacion` -- ni un sorteo de más. Es deliberado: así las
    pruebas de regresión de la Fase 5, que fijan secuencias exactas de
    aleatoriedad para semillas conocidas, no se ven afectadas por esta
    extensión a menos que alguien pida inserción/deleción explícitamente.
    """
    instruccion_final, hubo_sustitucion = copiar_con_mutacion(
        instruccion, tasa_sustitucion, longitud_genoma, rng
    )

    if tasa_insercion <= 0.0 and tasa_delecion <= 0.0:
        tipo = "sustitucion" if hubo_sustitucion else None
        return [instruccion_final], tipo

    if tasa_insercion > 0.0 and rng.random() < tasa_insercion:
        return [instruccion_final, instruccion_aleatoria(rng, longitud_genoma)], "insercion"

    if tasa_delecion > 0.0 and rng.random() < tasa_delecion:
        return [], "delecion"

    tipo = "sustitucion" if hubo_sustitucion else None
    return [instruccion_final], tipo
