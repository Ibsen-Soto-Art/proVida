"""Demo de la Fase 4, sub-fase 5: tareas lógicas como fuente de merit.

Genoma de mano (todavía sin auto-replicación, para aislar el mecanismo de
tareas) que resuelve las tres tareas del MVP a partir de dos inputs (a, b):

  NAND = nand(a, b)                       -- la instrucción primitiva misma
  AND  = NOT(NAND(a, b)) = nand(x, x)      -- aplicando NOT sobre el NAND
  NOT  = NOT(b)                            -- nand(b, b), usando el último input

Cada `output` se revisa contra el historial de inputs recientes. La
primera vez que un output coincide con una tarea, el merit se multiplica
por el bono correspondiente (ver provida/tasks/logicas.py).
"""

import random

from provida.tasks.ambiente import Ambiente
from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I

genoma = [
    I("input", ("AX",)),        # 0: AX = a
    I("input", ("BX",)),        # 1: BX = b
    I("nand", ("AX", "BX")),    # 2: AX = NAND(a, b)
    I("output", ("AX",)),       # 3: intenta resolver NAND
    I("mov", ("CX", "AX")),     # 4: CX = NAND(a, b)
    I("nand", ("CX", "CX")),    # 5: CX = NOT(NAND(a,b)) = AND(a, b)
    I("output", ("CX",)),       # 6: intenta resolver AND
    I("nand", ("BX", "BX")),    # 7: BX = NOT(b)
    I("output", ("BX",)),       # 8: intenta resolver NOT (último input = b)
    I("nop", ()),                # 9
]

ambiente = Ambiente()
cpu = CPU(genoma, rng=random.Random(11), ambiente=ambiente)

print(f"Merit inicial: {cpu.merit}")
for paso in range(9):
    cpu.step()
    print(
        f"  paso {paso}: {genoma[paso].opcode:10} "
        f"tareas resueltas hasta ahora = {sorted(cpu.tareas_resueltas)}  "
        f"merit = {cpu.merit}"
    )

print(f"\nMerit final: {cpu.merit}  (esperado: 2 * 4 * 8 = 64.0)")
assert cpu.tareas_resueltas == {"NOT", "AND", "NAND"}
assert cpu.merit == 64.0

print(
    "\nSi este organismo compitiera por turnos de CPU junto a otro que "
    "nunca resuelve ninguna tarea (merit=1.0), tendría 64 veces más "
    "probabilidad de ser elegido en cada sorteo del planificador -- y por "
    "lo tanto, en promedio, se reproduciría muchísimo más rápido."
)
