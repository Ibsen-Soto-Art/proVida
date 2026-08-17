import random

from provida.metrics.registro import RegistroEventos
from provida.vm.cpu import CPU

# Los 8 desplazamientos del vecindario de Moore (las 8 celdas alrededor de
# una posición, sin incluir la posición misma). Es el vecindario que usa
# Avida por defecto para decidir dónde nace una cría.
VECINDARIO_MOORE = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1), (0, 1),
    (1, -1), (1, 0), (1, 1),
]


class Mundo:
    """Grid 2D toroidal donde los organismos compiten por espacio y CPU.

    Toroidal = los bordes se conectan entre sí (la última columna es
    vecina de la primera, igual con filas). Es deliberado: sin esto, los
    organismos en el borde tendrían menos vecinos que los del centro, lo
    cual introduciría una ventaja o desventaja posicional artificial que
    no tiene nada que ver con la calidad del genoma -- justo el tipo de
    sesgo que no queremos si más adelante vamos a interpretar "quién se
    propaga más" como una señal de selección natural.
    """

    def __init__(
        self,
        ancho: int,
        alto: int,
        rng: random.Random | None = None,
        registro: RegistroEventos | None = None,
    ):
        self.ancho = ancho
        self.alto = alto
        self.celdas: list[list[CPU | None]] = [[None] * ancho for _ in range(alto)]
        self.rng = rng if rng is not None else random.Random()
        self.nacimientos = 0
        self.reemplazos = 0
        self.turno = 0

        # Registro de eventos opcional (Fase 6): si no se pasa ninguno, el
        # mundo funciona exactamente igual que antes -- observar la
        # simulación es un extra, no un requisito para que corra.
        self.registro = registro
        self._siguiente_id = 0

    def _nuevo_id(self) -> int:
        id_ = self._siguiente_id
        self._siguiente_id += 1
        return id_

    def colocar(self, cpu: CPU, fila: int, columna: int) -> None:
        if cpu.id_organismo is None:
            cpu.id_organismo = self._nuevo_id()
        self.celdas[fila][columna] = cpu

    def organismos_vivos(self) -> list[tuple[int, int, CPU]]:
        return [
            (fila, col, cpu)
            for fila in range(self.alto)
            for col in range(self.ancho)
            if (cpu := self.celdas[fila][col]) is not None
        ]

    def poblacion_actual(self) -> int:
        return len(self.organismos_vivos())

    def _vecino_aleatorio(self, fila: int, columna: int) -> tuple[int, int]:
        df, dc = self.rng.choice(VECINDARIO_MOORE)
        return (fila + df) % self.alto, (columna + dc) % self.ancho

    def ejecutar_ciclo(self, instrucciones_por_turno: int = 1) -> None:
        """Un turno del planificador: elige un organismo (ponderado por
        merit) y le hace ejecutar hasta `instrucciones_por_turno`
        instrucciones.

        No es una simulación de tiempo real ni de concurrencia -- es un
        sorteo ponderado (ver docs/arquitectura.md, sección 3). Un
        organismo con el doble de merit no ejecuta "al doble de velocidad"
        de forma determinista; tiene el doble de probabilidad de ser
        elegido en cada sorteo, lo cual en promedio produce el mismo
        efecto sobre muchos turnos.
        """
        self.turno += 1
        vivos = self.organismos_vivos()
        if not vivos:
            return

        pesos = [cpu.merit for _, _, cpu in vivos]
        fila, columna, cpu = self.rng.choices(vivos, weights=pesos, k=1)[0]

        for _ in range(instrucciones_por_turno):
            cpu.step()
            if cpu.replicacion_completa:
                # El resto del turno se pierde -- en Avida real, dividir
                # consume el resto del "time slice" del organismo.
                self._procesar_nacimiento(fila, columna, cpu)
                break

    def ejecutar_ciclos(self, n: int, instrucciones_por_turno: int = 1) -> None:
        for _ in range(n):
            self.ejecutar_ciclo(instrucciones_por_turno)

    def _procesar_nacimiento(self, fila: int, columna: int, cpu_padre: CPU) -> None:
        genoma_hijo = cpu_padre.genoma_hijo
        # Desde la Fase 7 la cría es una lista que crece con cada h-copy
        # (no un arreglo de tamaño fijo), así que "completa" ya no
        # significa "sin huecos" -- solo que no esté vacía (ver h-divide
        # en provida/vm/cpu.py).
        assert genoma_hijo is not None and len(genoma_hijo) > 0

        cpu_hijo = CPU(
            list(genoma_hijo),
            tasa_mutacion=cpu_padre.tasa_mutacion,
            rng=cpu_padre.rng,
            merit=cpu_padre.merit,
            ambiente=cpu_padre.ambiente,
            id_organismo=self._nuevo_id(),
            generacion=cpu_padre.generacion + 1,
            id_padre=cpu_padre.id_organismo,
            tasa_insercion=cpu_padre.tasa_insercion,
            tasa_delecion=cpu_padre.tasa_delecion,
        )
        # La cría hereda también qué tareas ya tiene "acreditadas" -- si no,
        # al ejecutar el mismo genoma y volver a resolver las mismas
        # tareas que su padre, cobraría el bono de nuevo, y el merit se
        # inflaría sin límite en cada generación aunque el comportamiento
        # sea idéntico. Una mutación SÍ puede hacer que la cría descubra
        # una tarea nueva que su linaje no tenía -- eso sigue pagando.
        cpu_hijo.tareas_resueltas = set(cpu_padre.tareas_resueltas)

        f_destino, c_destino = self._vecino_aleatorio(fila, columna)
        if self.celdas[f_destino][c_destino] is not None:
            self.reemplazos += 1
        self.celdas[f_destino][c_destino] = cpu_hijo
        self.nacimientos += 1

        if self.registro is not None:
            self.registro.registrar_nacimiento(self.turno, cpu_hijo, cpu_padre)

        # El padre "renace" para poder intentar reproducirse de nuevo:
        # conserva su genoma y su merit, pero su estado de ejecución
        # (registros, pila, heads, IP) se reinicia -- igual que la cría,
        # empieza otro ciclo de vida desde cero.
        cpu_padre.registros = {"AX": 0, "BX": 0, "CX": 0}
        cpu_padre.pila = []
        cpu_padre.ip = 0
        cpu_padre.read_head = 0
        cpu_padre.write_head = 0
        cpu_padre.genoma_hijo = None
        cpu_padre.replicacion_completa = False
