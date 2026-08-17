from provida.vm.instructions import MASCARA_REGISTRO

# Bono multiplicativo de merit por resolver cada tarea, la primera vez que
# un organismo lo logra. Multiplicativo (no aditivo) a propósito: en Avida
# real, resolver varias tareas compone la ventaja reproductiva en vez de
# sumarla -- un organismo que resuelve dos tareas no es "un poco mejor",
# es dramáticamente mejor. Los valores crecen con la dificultad relativa:
# NOT es la más simple de construir a partir de `nand` (nand(a,a)); AND y
# NAND requieren combinar más pasos.
BONUS_MERITO = {
    "NOT": 2.0,
    "AND": 4.0,
    "NAND": 8.0,
}

# Cuántos de los últimos inputs hace falta recordar para poder verificar
# la tarea que requiere más operandos (AND y NAND necesitan 2).
HISTORIAL_INPUTS_MAXIMO = 2


def tareas_resueltas_por_output(historial_inputs: list[int], valor_output: int) -> list[str]:
    """Determina qué tareas lógicas satisface `valor_output`, dado el
    historial de inputs recientes del organismo (el más reciente al final).

    Devuelve una lista (puede tener más de un nombre, o ninguno) -- es la
    CPU quien decide cuáles de esas ya habían sido cobradas antes por ese
    organismo en particular, no este módulo, que no tiene noción de
    "organismo".
    """
    resueltas = []

    if len(historial_inputs) >= 1:
        a = historial_inputs[-1]
        if valor_output == (~a) & MASCARA_REGISTRO:
            resueltas.append("NOT")

    if len(historial_inputs) >= 2:
        a, b = historial_inputs[-2], historial_inputs[-1]
        if valor_output == (a & b):
            resueltas.append("AND")
        if valor_output == (~(a & b)) & MASCARA_REGISTRO:
            resueltas.append("NAND")

    return resueltas
