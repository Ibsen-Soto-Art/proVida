"""Demo de la Fase 7: auto-replicación por direccionamiento de contenido.

A diferencia del genoma ancestral de la sub-fase 2 (que necesitaba
construir un contador CX igual a su propio tamaño, con el truco de
duplicación), este genoma NO sabe cuántas instrucciones tiene. El bucle
de copia se detiene cuando `jmp-vuelta-etiqueta` detecta que el read_head
completó una vuelta entera al genoma circular -- una condición estructural,
no un número memorizado de antemano.

Esto resuelve la limitación que documentamos en la Fase 2: como el
tamaño del genoma ya no está "hardcodeado" en ninguna parte, permite que
mutaciones de inserción/deleción cambien el tamaño del genoma sin romper
el mecanismo de auto-replicación (ver examples/demo_evolucion_tamano.py).
"""

from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I

GENOMA_ANCESTRAL_POR_ETIQUETAS = [
    I("h-alloc", ()),             # 0
    I("nop-a", ()),               # 1: marca "inicio del bucle de copia"
    I("h-copy", ()),              # 2
    I("jmp-vuelta-etiqueta", ()), # 3: ¿el read_head dio una vuelta completa?
    I("nop-a", ()),               # 4: etiqueta propia de la instrucción anterior
    I("jmp-etiqueta", ()),        # 5: si no, vuelve incondicionalmente al bucle
    I("nop-c", ()),               # 6: etiqueta propia de la instrucción anterior
    I("nop", ()),                 # 7: separador (no es un nop de etiqueta)
    I("nop-b", ()),               # 8: marca "salida del bucle"
    I("h-divide", ()),            # 9
]

cpu = CPU(GENOMA_ANCESTRAL_POR_ETIQUETAS)
pasos = cpu.run_hasta_replicar(max_pasos=300)

print(f"Longitud del genoma: {len(GENOMA_ANCESTRAL_POR_ETIQUETAS)} (nunca se usó ese número en el código)")
print(f"Pasos hasta replicarse: {pasos}")
print(f"Instrucciones copiadas: {len(cpu.genoma_hijo)}")
print(f"¿Cría idéntica al padre? {cpu.genoma_hijo == GENOMA_ANCESTRAL_POR_ETIQUETAS}")

assert cpu.replicacion_completa
assert cpu.genoma_hijo == GENOMA_ANCESTRAL_POR_ETIQUETAS

print(
    "\nA diferencia del genoma ancestral de la sub-fase 2, este no tiene "
    "ningún número que dependa de su propio tamaño -- si mañana insertamos "
    "o eliminamos una instrucción en cualquier parte, el mecanismo de "
    "copia sigue funcionando exactamente igual, porque la condición de "
    "parada es 'el read_head dio una vuelta completa', no 'copié N "
    "instrucciones'."
)
