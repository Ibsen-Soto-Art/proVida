import random

from provida.mutation.sustitucion import copiar_con_mutacion
from provida.tasks.ambiente import Ambiente
from provida.tasks.logicas import HISTORIAL_INPUTS_MAXIMO, BONUS_MERITO, tareas_resueltas_por_output
from provida.vm.instructions import MASCARA_REGISTRO, Instruccion


class CPU:
    """Estado de ejecución de un único organismo.

    El genoma es circular: al llegar a la última instrucción, el puntero
    de instrucción (IP) vuelve a la posición 0. Esto refleja el diseño
    real de Avida -- un organismo no tiene un "final de programa" natural;
    sigue ejecutando su código indefinidamente hasta que algo externo
    (el planificador de la población, que llega en una sub-fase futura)
    decide que deja de existir.
    """

    def __init__(
        self,
        genoma: list[Instruccion],
        tasa_mutacion: float = 0.0,
        rng: random.Random | None = None,
        merit: float = 1.0,
        ambiente: Ambiente | None = None,
    ):
        if not genoma:
            raise ValueError("El genoma no puede estar vacío: no habría IP válido.")
        self.genoma = genoma
        self.registros = {"AX": 0, "BX": 0, "CX": 0}
        self.pila: list[int] = []
        self.ip = 0
        self.instrucciones_ejecutadas = 0

        # Estado de auto-replicación. `genoma_hijo` es None hasta que el
        # organismo ejecuta `h-alloc` -- intentar copiar sin haber
        # reservado espacio antes es un error del genoma, no algo que la
        # CPU deba tolerar en silencio (ver `h-copy` más abajo).
        self.read_head = 0
        self.write_head = 0
        self.genoma_hijo: list[Instruccion | None] | None = None
        self.replicacion_completa = False

        # Mutación por sustitución (Fase 4, sub-fase 3). El valor por
        # defecto es 0.0 -- no 0.0075 -- para que la CPU sea determinista
        # a menos que alguien pida explícitamente lo contrario; así las
        # demos y pruebas de las sub-fases 1 y 2 (que asumen copia exacta)
        # siguen funcionando sin cambios.
        self.tasa_mutacion = tasa_mutacion
        self.rng = rng if rng is not None else random.Random()
        self.mutaciones_ocurridas = 0

        # Merit: determina la probabilidad de que el planificador de la
        # población elija a este organismo para ejecutar en cada turno
        # (ver provida/world/grid.py). Empieza uniforme (1.0 por defecto)
        # y las tareas lógicas resueltas lo multiplican (ver `output`).
        self.merit = merit

        # Ambiente y tareas lógicas (Fase 4, sub-fase 5). Sin ambiente,
        # `input`/`output` no tienen efecto -- un organismo cuyo genoma
        # las use, pero que se ejecute de forma aislada sin ambiente, no
        # debe fallar, solo no ganar merit por tareas.
        self.ambiente = ambiente
        self.ultimos_inputs: list[int] = []
        self.tareas_resueltas: set[str] = set()

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

        elif instr.opcode == "h-alloc":
            # Reserva un genoma hijo del mismo tamaño que el propio y
            # reinicia los heads. En el MVP el genoma nunca cambia de
            # tamaño (solo hay mutación por sustitución), así que reservar
            # exactamente `len(self.genoma)` casillas es suficiente -- en
            # un modelo con inserción/deleción habría que reservar de más.
            self.genoma_hijo = [None] * len(self.genoma)
            self.read_head = 0
            self.write_head = 0
            self.replicacion_completa = False

        elif instr.opcode == "h-copy":
            # Si no se reservó espacio antes (con h-alloc), la copia
            # simplemente no ocurre: un genoma "torpe" -- de fábrica, o
            # mutado -- no debe poder crashear la simulación entera. En
            # una población con muchos organismos ejecutándose de forma
            # continua e independiente, no hay quien valide de antemano
            # que cada uno llame a sus instrucciones en el orden "correcto".
            if self.genoma_hijo is not None:
                # Si la cría ya está llena, la copia tampoco tiene efecto
                # -- el read_head sigue avanzando (más abajo), pero no hay
                # dónde más escribir. Evita un IndexError por un genoma
                # que ejecuta más h-copy de los que necesita.
                if self.write_head < len(self.genoma_hijo):
                    instruccion_original = self.genoma[self.read_head]
                    instruccion_final, hubo_mutacion = copiar_con_mutacion(
                        instruccion_original, self.tasa_mutacion, len(self.genoma), self.rng
                    )
                    self.genoma_hijo[self.write_head] = instruccion_final
                    if hubo_mutacion:
                        self.mutaciones_ocurridas += 1
                    self.write_head += 1
            self.read_head = (self.read_head + 1) % len(self.genoma)

        elif instr.opcode == "h-divide":
            # La división solo se completa si la cría quedó totalmente
            # copiada. Si el organismo pide dividirse antes de tiempo (un
            # genoma "torpe", o -- en sub-fases futuras -- mutado de forma
            # que rompe su propio bucle de copia), la división simplemente
            # no ocurre: no es un error, es un organismo que falla en
            # reproducirse, que es exactamente lo que la selección natural
            # debe poder penalizar más adelante.
            if self.genoma_hijo is not None and all(i is not None for i in self.genoma_hijo):
                self.replicacion_completa = True

        elif instr.opcode == "input":
            (r,) = instr.args
            if self.ambiente is not None:
                valor = self.ambiente.generar_input(self.rng)
                self._escribir(r, valor)
                self.ultimos_inputs.append(valor)
                if len(self.ultimos_inputs) > HISTORIAL_INPUTS_MAXIMO:
                    self.ultimos_inputs.pop(0)

        elif instr.opcode == "output":
            (r,) = instr.args
            if self.ambiente is not None:
                valor = self._leer(r)
                for tarea in tareas_resueltas_por_output(self.ultimos_inputs, valor):
                    # Cada tarea solo paga la primera vez que este
                    # organismo la resuelve -- si no, bastaría con repetir
                    # el mismo output para inflar el merit sin límite.
                    if tarea not in self.tareas_resueltas:
                        self.tareas_resueltas.add(tarea)
                        self.merit *= BONUS_MERITO[tarea]

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

    def run_hasta_replicar(self, max_pasos: int) -> int:
        """Ejecuta hasta que `h-divide` complete una replicación, o se agote `max_pasos`.

        A diferencia de `run`, aquí el punto de parada sí es un concepto
        del dominio: "el organismo terminó de reproducirse" es un evento
        real, no un límite arbitrario. `max_pasos` sigue siendo necesario
        como salvaguarda -- un genoma mal formado (o, más adelante, mutado)
        podría no completar nunca la copia y quedar en bucle infinito.
        """
        pasos = 0
        while not self.replicacion_completa and pasos < max_pasos:
            self.step()
            pasos += 1
        return pasos
