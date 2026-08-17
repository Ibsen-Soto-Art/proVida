from provida.vm.instructions import Instruccion

# Los registros son enteros sin signo de 32 bits. No es un requisito del
# hardware (esto es una VM simulada en Python, que maneja enteros de
# precisión arbitraria por defecto) -- es una elección deliberada para que
# `nand` opere sobre un ancho de bits fijo y con sentido, y para que `add`/
# `inc` se desborden de forma predecible en vez de crecer sin límite.
ANCHO_REGISTRO_BITS = 32
MASCARA_REGISTRO = (1 << ANCHO_REGISTRO_BITS) - 1


class CPU:
    """Estado de ejecución de un único organismo.

    El genoma es circular: al llegar a la última instrucción, el puntero
    de instrucción (IP) vuelve a la posición 0. Esto refleja el diseño
    real de Avida -- un organismo no tiene un "final de programa" natural;
    sigue ejecutando su código indefinidamente hasta que algo externo
    (el planificador de la población, que llega en una sub-fase futura)
    decide que deja de existir.
    """

    def __init__(self, genoma: list[Instruccion]):
        if not genoma:
            raise ValueError("El genoma no puede estar vacío: no habría IP válido.")
        self.genoma = genoma
        self.registros = {"AX": 0, "BX": 0, "CX": 0}
        self.pila: list[int] = []
        self.ip = 0
        self.instrucciones_ejecutadas = 0

    def _leer(self, registro: str) -> int:
        return self.registros[registro]

    def _escribir(self, registro: str, valor: int) -> None:
        self.registros[registro] = valor & MASCARA_REGISTRO

    def step(self) -> None:
        """Ejecuta la instrucción en el IP actual y avanza el IP."""
        instr = self.genoma[self.ip]
        salto = None  # desplazamiento relativo, solo si la instrucción es un salto

        if instr.opcode == "nop":
            pass

        elif instr.opcode == "mov":
            rd, rs = instr.args
            self._escribir(rd, self._leer(rs))

        elif instr.opcode == "inc":
            (r,) = instr.args
            self._escribir(r, self._leer(r) + 1)

        elif instr.opcode == "dec":
            (r,) = instr.args
            self._escribir(r, self._leer(r) - 1)

        elif instr.opcode == "add":
            rd, rs = instr.args
            self._escribir(rd, self._leer(rd) + self._leer(rs))

        elif instr.opcode == "nand":
            # Única instrucción lógica del set (ver docs/arquitectura.md):
            # al ser funcionalmente completa, NOT/AND/etc. deben construirse
            # combinándola en vez de existir como instrucciones propias --
            # es lo que obliga a que resolver esas tareas sea un logro
            # evolutivo real y no una casilla que se marca sola.
            rd, rs = instr.args
            self._escribir(rd, ~(self._leer(rd) & self._leer(rs)))

        elif instr.opcode == "push":
            (r,) = instr.args
            self.pila.append(self._leer(r))

        elif instr.opcode == "pop":
            # Una pila vacía entrega 0 en vez de lanzar una excepción: un
            # organismo mutado que hace pop de más es un genoma "torpe",
            # no un error del intérprete -- debe poder seguir ejecutándose
            # (probablemente mal) en vez de crashear la simulación entera.
            (r,) = instr.args
            self._escribir(r, self.pila.pop() if self.pila else 0)

        elif instr.opcode == "jmp":
            (offset,) = instr.args
            salto = offset

        elif instr.opcode == "jmp-if-zero":
            r, offset = instr.args
            if self._leer(r) == 0:
                salto = offset

        else:
            raise ValueError(f"Opcode no soportado en esta sub-fase: {instr.opcode!r}")

        self.ip = (self.ip + (salto if salto is not None else 1)) % len(self.genoma)
        self.instrucciones_ejecutadas += 1

    def run(self, max_pasos: int) -> None:
        """Ejecuta hasta `max_pasos` instrucciones.

        `max_pasos` es un límite de conveniencia para poder observar la
        ejecución de forma acotada -- no es un concepto del dominio. Un
        organismo real (una vez exista el planificador de la población)
        no "termina": deja de ejecutarse cuando es reemplazado por otra
        cría, no porque agote un contador interno.
        """
        for _ in range(max_pasos):
            self.step()
