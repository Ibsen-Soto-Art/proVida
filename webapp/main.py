"""Demo web interactiva de proVida: transmite una simulación en vivo por
WebSocket, para verla evolucionar en el navegador en vez de solo leer una
gráfica ya terminada (eso es lo que hace sitio/, el reporte estático).

Cada conexión WebSocket obtiene su PROPIA simulación aislada (su propio
`Mundo`) -- así dos visitantes no interfieren entre sí, ni comparten
estado. El navegador solo dibuja lo que el servidor le manda; toda la
lógica de evolución sigue viviendo en provida/, sin duplicarse aquí.
"""

import asyncio
import json
import random

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from provida.tasks.ambiente import Ambiente
from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I
from provida.world.grid import Mundo

app = FastAPI()
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")

# Mismos dos genotipos del experimento de selección natural (Fase 4,
# sub-fase 6 / Fase 6): misma longitud exacta, para que la única ventaja
# real sea resolver la tarea, no copiarse más rápido.
CONTROL = [
    I("h-alloc", ()), I("nop", ()), I("nop", ()), I("nop", ()), I("nop", ()),
    I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
    I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
    I("nop", ()), I("nop", ()), I("nop", ()), I("nop", ()),
    I("jmp-if-zero", ("CX", 4)), I("h-copy", ()), I("dec", ("CX",)),
    I("jmp", (-3,)), I("h-divide", ()),
]
TAREA = [
    I("h-alloc", ()), I("input", ("AX",)), I("input", ("BX",)),
    I("nand", ("AX", "BX")), I("output", ("AX",)),
    I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
    I("inc", ("CX",)), I("add", ("CX", "CX")), I("add", ("CX", "CX")),
    I("nop", ()), I("nop", ()), I("nop", ()), I("nop", ()),
    I("jmp-if-zero", ("CX", 4)), I("h-copy", ()), I("dec", ("CX",)),
    I("jmp", (-3,)), I("h-divide", ()),
]

ANCHO = ALTO = 18
POSICIONES_FUNDADORAS = [
    (2, 2), (2, 15), (15, 2), (15, 15),
    (8, 2), (2, 8), (15, 8), (8, 15),
]
TURNOS_POR_CUADRO = 250
INTERVALO_SEGUNDOS = 0.08


def crear_mundo(tasa_mutacion: float) -> Mundo:
    rng = random.Random()
    ambiente = Ambiente()
    mundo = Mundo(ancho=ANCHO, alto=ALTO, rng=rng)
    for i, (fila, columna) in enumerate(POSICIONES_FUNDADORAS):
        genoma = CONTROL if i % 2 == 0 else TAREA
        mundo.colocar(CPU(genoma, tasa_mutacion=tasa_mutacion, rng=rng, ambiente=ambiente), fila, columna)
    return mundo


def serializar(mundo: Mundo) -> dict:
    """Reduce el estado de la población a lo mínimo que el navegador
    necesita para dibujar un cuadro: una categoría por celda, no el
    genoma completo -- así el mensaje por WebSocket se queda pequeño
    incluso a varios cuadros por segundo."""
    celdas = []
    for fila in range(mundo.alto):
        for columna in range(mundo.ancho):
            cpu = mundo.celdas[fila][columna]
            if cpu is None:
                celdas.append(None)
            elif "NAND" in cpu.tareas_resueltas:
                celdas.append("tarea")
            elif cpu.genoma == TAREA:
                celdas.append("tarea_sin_resolver")
            else:
                celdas.append("control")

    vivos = mundo.organismos_vivos()
    merit_promedio = sum(cpu.merit for _, _, cpu in vivos) / len(vivos) if vivos else 0.0
    return {
        "ancho": mundo.ancho,
        "alto": mundo.alto,
        "celdas": celdas,
        "turno": mundo.turno,
        "poblacion": len(vivos),
        "merit_promedio": round(merit_promedio, 2),
    }


async def receptor(websocket: WebSocket, estado: dict) -> None:
    """Corre en paralelo al bucle principal, escuchando mensajes de
    control del navegador (pausar/reanudar/reiniciar) sin bloquear el
    envío de cuadros."""
    async for mensaje in websocket.iter_text():
        try:
            datos = json.loads(mensaje)
        except json.JSONDecodeError:
            continue
        estado["accion"] = datos.get("accion")
        if "tasa_mutacion" in datos:
            estado["tasa_mutacion"] = float(datos["tasa_mutacion"])


@app.get("/")
async def index():
    return FileResponse("webapp/static/index.html")


@app.websocket("/ws")
async def simular(websocket: WebSocket):
    await websocket.accept()
    estado = {"accion": None, "tasa_mutacion": 0.0075}
    tarea_receptor = asyncio.create_task(receptor(websocket, estado))

    mundo = crear_mundo(estado["tasa_mutacion"])
    corriendo = True

    try:
        while True:
            accion = estado.pop("accion", None)
            if accion == "pausar":
                corriendo = False
            elif accion == "reanudar":
                corriendo = True
            elif accion == "reiniciar":
                mundo = crear_mundo(estado["tasa_mutacion"])
                corriendo = True

            if corriendo:
                mundo.ejecutar_ciclos(TURNOS_POR_CUADRO, instrucciones_por_turno=3)

            await websocket.send_json(serializar(mundo))
            await asyncio.sleep(INTERVALO_SEGUNDOS)
    except WebSocketDisconnect:
        pass
    finally:
        tarea_receptor.cancel()
