import math

# Ancho del rango de temperaturas que un organismo puede llegar a "declarar"
# como su óptimo (ver valor_a_temperatura). No tiene un significado físico
# -- es una elección de escala, igual que decidir que los registros son de
# 32 bits. Rango resultante: aproximadamente [-50, 50).
RANGO_TEMPERATURA = 100.0

# Desviación estándar de la campana de tolerancia térmica, en las mismas
# unidades que la temperatura. Cuanto más ancha, más indulgente es el
# ambiente con organismos mal adaptados -- un valor grande hace que la
# temperatura casi no importe; uno muy chico hace la selección brutal.
ANCHO_TOLERANCIA_POR_DEFECTO = 15.0


def valor_a_temperatura(valor_registro: int) -> float:
    """Convierte el valor crudo de un registro (0..2^32-1) en una
    temperatura dentro de un rango acotado y con sentido, usando módulo --
    así un organismo no necesita evitar el desbordamiento a propósito;
    cualquier valor que construya con inc/dec/add cae en algún punto del
    rango de todas formas.
    """
    return (valor_registro % int(RANGO_TEMPERATURA)) - RANGO_TEMPERATURA / 2


def factor_temperatura(
    temperatura_optima: float | None,
    temperatura_actual: float,
    ancho_tolerancia: float = ANCHO_TOLERANCIA_POR_DEFECTO,
) -> float:
    """Multiplicador de merit según qué tan lejos está la temperatura
    óptima del organismo de la temperatura actual del ambiente -- una
    campana de Gauss centrada en `temperatura_optima`: 1.0 si coinciden
    exactamente, decae suavemente (nunca llega a 0 en seco) mientras más
    se alejan.

    `temperatura_optima=None` significa "este organismo nunca declaró una
    preferencia" (no ejecutó `set-temperatura`) -- se trata como neutral
    (factor 1.0, sin penalización ni bono) para no afectar a ningún
    organismo de las fases anteriores a esta extensión.
    """
    if temperatura_optima is None:
        return 1.0
    diferencia = temperatura_optima - temperatura_actual
    return math.exp(-0.5 * (diferencia / ancho_tolerancia) ** 2)
