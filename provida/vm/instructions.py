from typing import NamedTuple


class Instruccion(NamedTuple):
    """Una instrucción del genoma: un opcode y sus operandos.

    Se representa como tupla (vía NamedTuple) y no como una clase con
    comportamiento propio porque el genoma necesita ser un dato plano:
    en sub-fases futuras hay que poder copiarlo instrucción por
    instrucción, mutarlo y compararlo entre organismos. Una instrucción
    no "sabe" ejecutarse a sí misma -- es la CPU quien interpreta el
    opcode, igual que un ribosoma interpreta un codón sin que el codón
    mismo contenga la maquinaria para traducirse.
    """

    opcode: str
    args: tuple = ()


# Aridad (número de operandos) de cada opcode soportado en esta sub-fase.
# Sirve de referencia y de validación rápida al construir genomas a mano;
# las instrucciones de auto-replicación (h-alloc, h-copy, h-divide) y de
# entrada/salida (input, output) se añaden en las sub-fases 2 y 5, cuando
# hay una CPU capaz de darles sentido.
ARIDAD_OPCODES = {
    "nop": 0,
    "mov": 2,
    "inc": 1,
    "dec": 1,
    "add": 2,
    "nand": 2,
    "push": 1,
    "pop": 1,
    "jmp": 1,
    "jmp-if-zero": 2,
}
