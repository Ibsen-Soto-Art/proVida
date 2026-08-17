"""Demo de la Fase 4, sub-fase 3: mutación durante la auto-replicación.

Dos partes:
1. Una sola replicación con una tasa de mutación alta (5%, para que sea
   visible en un genoma de solo 13 instrucciones) -- se muestra la
   diferencia exacta entre el genoma del padre y el de la cría.
2. Muchas replicaciones con la tasa por defecto de Avida (0.75%) para
   verificar que la tasa empírica de mutaciones converge al valor
   esperado -- una forma simple de "probar" que el mecanismo probabilístico
   está bien calibrado, no solo que compila.
"""

import random

from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I

GENOMA_ANCESTRAL = [
    I("h-alloc", ()),
    I("inc", ("CX",)),
    I("add", ("CX", "CX")),
    I("inc", ("CX",)),
    I("add", ("CX", "CX")),
    I("add", ("CX", "CX")),
    I("inc", ("CX",)),
    I("jmp-if-zero", ("CX", 4)),
    I("h-copy", ()),
    I("dec", ("CX",)),
    I("jmp", (-3,)),
    I("h-divide", ()),
    I("nop", ()),
]

print("=== Parte 1: una replicación con tasa de mutación alta (5%) ===")
cpu = CPU(GENOMA_ANCESTRAL, tasa_mutacion=0.05, rng=random.Random(7))
cpu.run_hasta_replicar(max_pasos=200)

print(f"Mutaciones intentadas durante la copia: {cpu.mutaciones_ocurridas}")
for i, (original, copia) in enumerate(zip(cpu.genoma, cpu.genoma_hijo)):
    marca = "  <- cambió" if original != copia else ""
    print(f"  [{i:2}] {original} -> {copia}{marca}")

print("\n=== Parte 2: tasa empírica sobre 2000 replicaciones (tasa nominal 0.75%) ===")
rng = random.Random(42)
TASA_NOMINAL = 0.0075
N_REPLICACIONES = 2000
total_mutaciones = 0
total_instrucciones_copiadas = 0

for _ in range(N_REPLICACIONES):
    cpu = CPU(GENOMA_ANCESTRAL, tasa_mutacion=TASA_NOMINAL, rng=rng)
    cpu.run_hasta_replicar(max_pasos=200)
    total_mutaciones += cpu.mutaciones_ocurridas
    total_instrucciones_copiadas += cpu.write_head

tasa_empirica = total_mutaciones / total_instrucciones_copiadas
print(f"Instrucciones copiadas en total: {total_instrucciones_copiadas}")
print(f"Mutaciones ocurridas en total: {total_mutaciones}")
print(f"Tasa empírica: {tasa_empirica:.4%}  (nominal: {TASA_NOMINAL:.4%})")
