from typing import NamedTuple

# Los registros son enteros sin signo de 32 bits. Vive aquí (y no en cpu.py)
# porque tanto la CPU como el verificador de tareas lógicas (provida/tasks)
# necesitan conocer el ancho de palabra, y este módulo no depende de
# ninguno de los dos -- evita una dependencia circular entre ellos.
ANCHO_REGISTRO_BITS = 32
MASCARA_REGISTRO = (1 << ANCHO_REGISTRO_BITS) - 1


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


# Aridad (número de operandos) de cada opcode del set completo del MVP.
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
    # Instrucciones de auto-replicación (Fase 4, sub-fase 2): permiten que
    # un organismo lea su propio genoma y escriba una copia en un espacio
    # nuevo, sin operar sobre registros -- por eso no llevan operandos.
    "h-alloc": 0,
    "h-copy": 0,
    "h-divide": 0,
    # Entrada/salida con el ambiente (Fase 4, sub-fase 5): permiten que un
    # organismo reciba bits del entorno y entregue resultados, que el
    # ambiente evalúa contra las tareas lógicas conocidas.
    "input": 1,
    "output": 1,
}
