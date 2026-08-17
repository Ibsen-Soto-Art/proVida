"""Demo de la Fase 4, sub-fase 1: una VM ejecutando un genoma fijo.

El genoma implementa un bucle "cuenta hacia abajo, suma hacia arriba":
construye BX = 5 a pulso (con `inc`, porque el set de instrucciones no
tiene una instrucción de "cargar constante" -- ver docs/arquitectura.md),
y luego, mientras BX no sea cero, incrementa AX y decrementa BX. Al
terminar, AX debería valer 5 y BX debería valer 0.

Sirve para demostrar, con un ejemplo mínimo, que la CPU maneja
correctamente registros, aritmética, y control de flujo con saltos
relativos -- antes de meter auto-replicación, mutación o población.
"""

from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I

genoma = [
    I("inc", ("BX",)),              # 0: BX=1
    I("inc", ("BX",)),              # 1: BX=2
    I("inc", ("BX",)),              # 2: BX=3
    I("inc", ("BX",)),              # 3: BX=4
    I("inc", ("BX",)),              # 4: BX=5
    I("jmp-if-zero", ("BX", 4)),    # 5: si BX==0, salta a la 9 (nop, fin del bucle)
    I("inc", ("AX",)),              # 6
    I("dec", ("BX",)),              # 7
    I("jmp", (-3,)),                # 8: vuelve a la 5 (revisar condición de nuevo)
    I("nop", ()),                   # 9: fin del bucle
]

cpu = CPU(genoma)

# 5 pasos para construir BX=5, más 5 iteraciones del bucle (4 pasos cada
# una: chequeo + inc + dec + jmp) más el chequeo final que sí sale = 5 + 21 = 26
cpu.run(26)

print(f"AX = {cpu.registros['AX']}  (esperado: 5)")
print(f"BX = {cpu.registros['BX']}  (esperado: 0)")
print(f"Instrucciones ejecutadas: {cpu.instrucciones_ejecutadas}")
print(f"IP tras terminar: {cpu.ip} (instrucción 'nop', índice 9)")

assert cpu.registros["AX"] == 5
assert cpu.registros["BX"] == 0

# Como el genoma es circular, un paso más no falla -- vuelve al principio
# (índice 0, el primer 'inc BX') y el ciclo entero empezaría de nuevo.
cpu.step()
print(f"\nUn paso más allá del 'fin': IP = {cpu.ip} (vuelve al índice 0, es circular)")
assert cpu.ip == 0
