import random

from provida.mutation.sustitucion import procesar_copia
from provida.tasks.ambiente import Ambiente
from provida.tasks.logicas import HISTORIAL_INPUTS_MAXIMO, BONUS_MERITO, tareas_resueltas_por_output
from provida.tasks.temperatura import valor_a_temperatura
from provida.vm.instructions import COMPLEMENTO_NOP, MASCARA_REGISTRO, NOPS_ETIQUETA, Instruccion

# Límite de seguridad para el crecimiento del genoma hijo (Fase 7): un
# organismo cuyo bucle de copia nunca detecta "vuelta completa" (por una
# etiqueta rota, por ejemplo) podría seguir copiando para siempre. Este
# tope no es un concepto biológico -- es una salvaguarda de que la
# simulación no consuma memoria sin límite por un genoma patológico.
LONGITUD_MAXIMA_HIJO_RELATIVA = 4
LONGITUD_MINIMA_HIJO = 1


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
        id_organismo: int | None = None,
        generacion: int = 0,
        id_padre: int | None = None,
        tasa_insercion: float = 0.0,
        tasa_delecion: float = 0.0,
        temperatura_optima: float | None = None,
    ):
        if not genoma:
            raise ValueError("El genoma no puede estar vacío: no habría IP válido.")
        self.genoma = genoma
        self.registros = {"AX": 0, "BX": 0, "CX": 0}
        self.pila: list[int] = []
        self.ip = 0
        self.instrucciones_ejecutadas = 0

        # Estado de auto-replicación. `genoma_hijo` es None hasta que el
        # organismo ejecuta `h-alloc`. A partir de la Fase 7 es una lista
        # que CRECE con cada h-copy (no un arreglo de tamaño fijo) --
        # necesario para que la inserción/deleción puedan cambiar el
        # tamaño de la cría. Intentar copiar sin haber reservado espacio
        # antes no es un error -- ver `h-copy` más abajo.
        self.read_head = 0
        self.write_head = 0
        self.genoma_hijo: list[Instruccion] | None = None
        self.replicacion_completa = False

        # Mutación por sustitución (Fase 4, sub-fase 3), y por
        # inserción/deleción (Fase 7). Los valores por defecto son 0.0
        # para que la CPU sea determinista a menos que alguien pida
        # explícitamente lo contrario; así las demos y pruebas de las
        # sub-fases anteriores (que asumen copia exacta) siguen
        # funcionando sin cambios.
        self.tasa_mutacion = tasa_mutacion
        self.tasa_insercion = tasa_insercion
        self.tasa_delecion = tasa_delecion
        self.rng = rng if rng is not None else random.Random()
        self.mutaciones_ocurridas = 0
        self.mutaciones_sustitucion = 0
        self.mutaciones_insercion = 0
        self.mutaciones_delecion = 0

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

        # Temperatura óptima declarada por el organismo (extensión post-
        # Fase 8). None significa "nunca ejecutó set-temperatura" --
        # tratado como neutral por provida.tasks.temperatura.factor_temperatura,
        # así que un organismo (o un genoma entero de las fases anteriores)
        # que nunca usa esta instrucción no se ve afectado en absoluto.
        self.temperatura_optima = temperatura_optima

        # Metadatos de linaje (Fase 6): no afectan la ejecución en absoluto
        # -- son puramente para observabilidad (el registro de eventos y el
        # árbol filogenético). `generacion` es la profundidad del linaje
        # (cuántos ancestros hasta el fundador), no un contador de tiempo
        # global sincronizado -- ver docs/glosario.md.
        self.id_organismo = id_organismo
        self.generacion = generacion
        self.id_padre = id_padre

    def _leer(self, registro: str) -> int:
        return self.registros[registro]

    def _escribir(self, registro: str, valor: int) -> None:
        self.registros[registro] = valor & MASCARA_REGISTRO

    def _leer_etiqueta_propia(self) -> list[str]:
        """Lee los nop-a/b/c que siguen inmediatamente a la instrucción
        actual -- esa secuencia es "mi etiqueta". Se detiene en la primera
        instrucción que no sea un nop de etiqueta."""
        etiqueta = []
        pos = (self.ip + 1) % len(self.genoma)
        for _ in range(len(self.genoma)):
            opcode = self.genoma[pos].opcode
            if opcode not in NOPS_ETIQUETA:
                break
            etiqueta.append(opcode)
            pos = (pos + 1) % len(self.genoma)
        return etiqueta

    def _buscar_complemento(self, etiqueta: list[str]) -> int | None:
        """Busca, circularmente, la primera aparición de la secuencia
        COMPLEMENTARIA a `etiqueta` en el genoma, empezando justo después
        de la etiqueta propia. Devuelve la posición justo después de esa
        aparición (el destino del salto), o None si no se encontró -- una
        etiqueta vacía o rota simplemente no tiene destino."""
        if not etiqueta:
            return None
        complemento = [COMPLEMENTO_NOP[nop] for nop in etiqueta]
        n = len(self.genoma)
        m = len(complemento)
        inicio = (self.ip + 1 + len(etiqueta)) % n
        for desplazamiento in range(n):
            pos = (inicio + desplazamiento) % n
            if [self.genoma[(pos + k) % n].opcode for k in range(m)] == complemento:
                return (pos + m) % n
        return None

    def step(self) -> None:
        """Ejecuta la instrucción en el IP actual y avanza el IP."""
        instr = self.genoma[self.ip]
        salto = None  # desplazamiento relativo, solo si la instrucción es un salto
        salto_absoluto = None  # posición absoluta, solo para saltos por etiqueta (Fase 7)

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
            # Empieza la cría vacía y reinicia los heads. Antes de la
            # Fase 7 esto reservaba un arreglo de tamaño fijo -- ahora la
            # cría crece con cada h-copy, así que no hace falta (ni tiene
            # sentido) saber su tamaño final de antemano.
            self.genoma_hijo = []
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
                tope = LONGITUD_MAXIMA_HIJO_RELATIVA * len(self.genoma)
                if len(self.genoma_hijo) < tope:
                    instruccion_original = self.genoma[self.read_head]
                    nuevas_instrucciones, tipo_evento = procesar_copia(
                        instruccion_original,
                        self.tasa_mutacion,
                        len(self.genoma),
                        self.rng,
                        tasa_insercion=self.tasa_insercion,
                        tasa_delecion=self.tasa_delecion,
                    )
                    self.genoma_hijo.extend(nuevas_instrucciones)
                    self.write_head = len(self.genoma_hijo)
                    if tipo_evento is not None:
                        self.mutaciones_ocurridas += 1
                        if tipo_evento == "sustitucion":
                            self.mutaciones_sustitucion += 1
                        elif tipo_evento == "insercion":
                            self.mutaciones_insercion += 1
                        elif tipo_evento == "delecion":
                            self.mutaciones_delecion += 1
            self.read_head = (self.read_head + 1) % len(self.genoma)

        elif instr.opcode == "h-divide":
            # A partir de la Fase 7, la división se completa con
            # cualquier cría no vacía -- ya no hay un tamaño objetivo
            # numérico contra el cual comparar (ver docs/arquitectura.md).
            # Es el propio organismo quien decide cuándo copiar lo
            # suficiente antes de dividirse (con jmp-vuelta-etiqueta, por
            # ejemplo); h-divide confía en esa decisión, igual que Avida
            # real. Un genoma que divide con una cría casi vacía obtiene
            # una cría defectuosa -- eso lo penaliza la selección, no el
            # mecanismo de copia.
            if self.genoma_hijo is not None and len(self.genoma_hijo) >= LONGITUD_MINIMA_HIJO:
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

        elif instr.opcode in ("nop-a", "nop-b", "nop-c"):
            pass  # marcadores de etiqueta: no hacen nada al ejecutarse

        elif instr.opcode == "jmp-etiqueta":
            destino = self._buscar_complemento(self._leer_etiqueta_propia())
            if destino is not None:
                salto_absoluto = destino

        elif instr.opcode == "jmp-cero-etiqueta":
            (r,) = instr.args
            if self._leer(r) == 0:
                destino = self._buscar_complemento(self._leer_etiqueta_propia())
                if destino is not None:
                    salto_absoluto = destino

        elif instr.opcode == "set-temperatura":
            # A diferencia de las tareas lógicas, esto no depende de un
            # ambiente ni de inputs externos -- es un rasgo propio del
            # organismo, calculado con sus propios registros. El ambiente
            # (si existe) es quien decide más tarde, en cada turno del
            # planificador, qué tan bien le sienta este valor -- ver
            # provida/world/grid.py y provida/tasks/temperatura.py.
            (r,) = instr.args
            self.temperatura_optima = valor_a_temperatura(self._leer(r))

        elif instr.opcode == "jmp-vuelta-etiqueta":
            # Salta solo si el read_head completó una vuelta entera al
            # genoma circular (volvió a 0 tras haber copiado al menos una
            # instrucción) -- la condición de salida del bucle de
            # auto-copia, sin necesitar contar cuántas instrucciones tiene
            # el genoma (ver el genoma ancestral por etiquetas).
            if self.genoma_hijo and self.read_head == 0:
                destino = self._buscar_complemento(self._leer_etiqueta_propia())
                if destino is not None:
                    salto_absoluto = destino

        else:
            raise ValueError(f"Opcode no soportado en esta sub-fase: {instr.opcode!r}")

        if salto_absoluto is not None:
            self.ip = salto_absoluto % len(self.genoma)
        else:
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
