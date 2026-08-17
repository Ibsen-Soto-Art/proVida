"""Demo de la Fase 4, sub-fase 2: un organismo que se copia a sí mismo.

Este es el "organismo ancestral" de proVida: el genoma más simple posible
que se auto-replica por completo, todavía sin mutación (eso es la
sub-fase 3) y todavía sin población (sub-fase 4) -- aquí solo queremos
demostrar, de forma aislada, que el mecanismo de copia funciona y produce
una cría idéntica al padre.

Nota de diseño importante: como elegimos direccionamiento indexado simple
(no nop-labels, ver docs/arquitectura.md), el genoma no puede "descubrir"
su propio tamaño en tiempo de ejecución -- tiene que traerlo precalculado.
Construirlo a puro `inc` (uno por instrucción) es imposible de cuadrar
exactamente con el tamaño total del genoma (el propio contador ocupa
instrucciones que también hay que contar). La solución: construir el
contador duplicando con `add CX, CX`, que llega al número exacto (13) con
muchas menos instrucciones que puro conteo unario.
"""

from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I

genoma_ancestral = [
    I("h-alloc", ()),               # 0: reserva espacio para la cría

    # Construye CX = 13 (el tamaño total de este genoma) duplicando en vez
    # de contar de a uno: 0->1->2->3->6->12->13
    I("inc", ("CX",)),              # 1: CX=1
    I("add", ("CX", "CX")),         # 2: CX=2
    I("inc", ("CX",)),              # 3: CX=3
    I("add", ("CX", "CX")),         # 4: CX=6
    I("add", ("CX", "CX")),         # 5: CX=12
    I("inc", ("CX",)),              # 6: CX=13

    # Bucle de copia: mientras CX > 0, copia una instrucción y decrementa.
    I("jmp-if-zero", ("CX", 4)),    # 7: si CX==0, salta a la 11 (h-divide)
    I("h-copy", ()),                # 8
    I("dec", ("CX",)),              # 9
    I("jmp", (-3,)),                # 10: vuelve a la 7

    I("h-divide", ()),              # 11: termina la replicación si la copia está completa
    I("nop", ()),                   # 12: relleno, nunca se alcanza en esta demo
]

assert len(genoma_ancestral) == 13, "el contador CX se construyó asumiendo este tamaño exacto"

cpu = CPU(genoma_ancestral)
pasos = cpu.run_hasta_replicar(max_pasos=200)

print(f"Replicación completa: {cpu.replicacion_completa}")
print(f"Pasos ejecutados: {pasos}")
print(f"Instrucciones copiadas (write_head): {cpu.write_head} / {len(genoma_ancestral)}")
print(f"¿La cría es idéntica al padre? {cpu.genoma_hijo == cpu.genoma}")

assert cpu.replicacion_completa
assert cpu.genoma_hijo == cpu.genoma
