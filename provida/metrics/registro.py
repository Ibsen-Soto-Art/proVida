from dataclasses import dataclass, field


@dataclass
class RegistroEventos:
    """Bitácora de una simulación, para analizar después de correrla.

    Deliberadamente no calcula promedios, gráficas ni estadísticas en el
    momento -- solo acumula datos crudos (un nacimiento es un nacimiento;
    una foto de la población es una foto). El análisis se hace aparte
    (ver examples/demo_laboratorio.py) para que el motor de simulación
    (provida/world/grid.py) no tenga que saber nada sobre matplotlib,
    pandas o networkx.
    """

    nacimientos: list[dict] = field(default_factory=list)
    snapshots: list[dict] = field(default_factory=list)

    def registrar_nacimiento(self, turno: int, cpu_hijo, cpu_padre) -> None:
        self.nacimientos.append({
            "turno": turno,
            "id": cpu_hijo.id_organismo,
            "id_padre": cpu_padre.id_organismo,
            "generacion": cpu_hijo.generacion,
            "merit": cpu_hijo.merit,
            "tareas_resueltas": frozenset(cpu_hijo.tareas_resueltas),
        })

    def registrar_snapshot(self, turno: int, mundo) -> None:
        vivos = mundo.organismos_vivos()
        poblacion = len(vivos)
        merit_promedio = sum(cpu.merit for _, _, cpu in vivos) / poblacion if poblacion else 0.0

        conteo_tareas: dict[str, int] = {}
        for _, _, cpu in vivos:
            for tarea in cpu.tareas_resueltas:
                conteo_tareas[tarea] = conteo_tareas.get(tarea, 0) + 1

        self.snapshots.append({
            "turno": turno,
            "poblacion": poblacion,
            "merit_promedio": merit_promedio,
            "conteo_tareas": conteo_tareas,
        })
