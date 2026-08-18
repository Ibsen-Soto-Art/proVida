"""Demo web interactiva de proVida: transmite una simulación en vivo por
WebSocket, para verla evolucionar en el navegador en vez de solo leer una
gráfica ya terminada (eso es lo que hace sitio/, el reporte estático).

Cada conexión WebSocket obtiene su PROPIA simulación aislada (su propio
`Mundo`) -- así dos visitantes no interfieren entre sí, ni comparten
estado. El navegador solo dibuja lo que el servidor le manda; toda la
lógica de evolución sigue viviendo en provida/, sin duplicarse aquí.

Dos "modos" de selección, mutuamente excluyentes -- combinarlos en un
solo experimento (4 genotipos a la vez) sería más rico pero mucho más
difícil de leer en una rejilla pequeña, así que cada modo tiene sus
propios genotipos y controles:

  - "tarea": el original -- NAND resuelto o no (ver Fase 4, sub-fase 6).
  - "temperatura": frío vs. cálido, con un ambiente que se puede
    calentar o enfriar en vivo (ver examples/demo_temperatura.py).
"""

import asyncio
import json
import random

from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketState

from provida.tasks.ambiente import Ambiente
from provida.tasks.temperatura import factor_temperatura
from provida.vm.cpu import CPU
from provida.vm.instructions import Instruccion as I
from provida.world.grid import Mundo

# Todo vive bajo el prefijo /vivo -- no porque a la app le importe, sino
# porque en el VPS comparte dominio con el sitio estático (Fase 8), que
# ya ocupa la raíz. Nginx reenvía /vivo/* aquí tal cual, sin recortar el
# prefijo, así que las rutas de FastAPI tienen que incluirlo también
# (ver docs/despliegue.md).
router = APIRouter(prefix="/vivo")

app = FastAPI()
app.mount("/vivo/static", StaticFiles(directory="webapp/static"), name="static")

# Límite de conexiones simultáneas (buena práctica antes de exponer esto
# en un VPS compartido con otros proyectos): cada conexión mantiene su
# propia simulación corriendo indefinidamente en el servidor mientras
# el visitante tenga la pestaña abierta -- sin un tope, muchas pestañas
# abiertas a la vez podrían acaparar CPU del servidor.
MAXIMO_CONEXIONES_SIMULTANEAS = 20
conexiones_activas = 0

ANCHO = ALTO = 18
POSICIONES_FUNDADORAS = [
    (2, 2), (2, 15), (15, 2), (15, 15),
    (8, 2), (2, 8), (15, 8), (8, 15),
]
INTERVALO_SEGUNDOS = 0.08

# --------------------------------------------------------------------
# Modo "tarea": dos genotipos de la misma longitud, uno resuelve NAND.
# --------------------------------------------------------------------
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
TURNOS_POR_CUADRO_TAREA = 250

# --------------------------------------------------------------------
# Modo "temperatura": frío vs. cálido (ver examples/demo_temperatura.py).
# Genoma ancestral por etiquetas (Fase 7) -- no necesita contar sus
# propias instrucciones, así que el segmento que construye AX puede
# tener cualquier longitud (con relleno para igualar entre genotipos).
# --------------------------------------------------------------------


def _construir_valor(registro: str, objetivo: int) -> list[I]:
    bits = bin(objetivo)[2:]
    instrucciones = [I("inc", (registro,))]
    for bit in bits[1:]:
        instrucciones.append(I("add", (registro, registro)))
        if bit == "1":
            instrucciones.append(I("inc", (registro,)))
    return instrucciones


_OBJETIVOS_TEMPERATURA = {"frio": 35, "calido": 65}  # -> -15.0°C y +15.0°C
_SEGMENTOS_TEMPERATURA = {n: _construir_valor("AX", v) for n, v in _OBJETIVOS_TEMPERATURA.items()}
_LONGITUD_MAXIMA_SEGMENTO = max(len(s) for s in _SEGMENTOS_TEMPERATURA.values())


def _genoma_temperatura(nombre: str) -> list[I]:
    construccion = _SEGMENTOS_TEMPERATURA[nombre]
    relleno = [I("nop", ())] * (_LONGITUD_MAXIMA_SEGMENTO - len(construccion))
    return (
        [I("h-alloc", ())]
        + construccion + relleno
        + [I("set-temperatura", ("AX",))]
        + [I("nop-a", ()), I("h-copy", ()), I("jmp-vuelta-etiqueta", ()), I("nop-a", ()),
           I("jmp-etiqueta", ()), I("nop-c", ()), I("nop", ()), I("nop-b", ()), I("h-divide", ())]
    )


FRIO = _genoma_temperatura("frio")
CALIDO = _genoma_temperatura("calido")
# El mecanismo de etiquetas (búsqueda de complemento en cada salto) es
# bastante más costoso por instrucción que los saltos numéricos del modo
# "tarea" -- menos turnos por cuadro para que cada cuadro siga tomando
# un tiempo de cómputo parecido y la demo no se sienta más lenta.
TURNOS_POR_CUADRO_TEMPERATURA = 60


def crear_mundo(estado: dict) -> tuple[Mundo, Ambiente, str]:
    modo = estado["modo"]
    rng = random.Random()
    mundo = Mundo(ancho=ANCHO, alto=ALTO, rng=rng)

    if modo == "temperatura":
        ambiente = Ambiente(
            temperatura_inicial=estado["temperatura_inicial"],
            tasa_cambio_temperatura=estado["tasa_cambio_temperatura"],
        )
        for i, (fila, columna) in enumerate(POSICIONES_FUNDADORAS):
            genoma = FRIO if i % 2 == 0 else CALIDO
            mundo.colocar(CPU(genoma, tasa_mutacion=estado["tasa_mutacion"], rng=rng, ambiente=ambiente), fila, columna)
    else:
        ambiente = Ambiente()
        for i, (fila, columna) in enumerate(POSICIONES_FUNDADORAS):
            genoma = CONTROL if i % 2 == 0 else TAREA
            mundo.colocar(CPU(genoma, tasa_mutacion=estado["tasa_mutacion"], rng=rng, ambiente=ambiente), fila, columna)

    return mundo, ambiente, modo


def serializar(mundo: Mundo, ambiente: Ambiente, modo: str) -> dict:
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
            elif modo == "temperatura":
                celdas.append("frio" if cpu.temperatura_optima is not None and cpu.temperatura_optima < 0 else "calido")
            elif "NAND" in cpu.tareas_resueltas:
                celdas.append("tarea")
            elif cpu.genoma == TAREA:
                celdas.append("tarea_sin_resolver")
            else:
                celdas.append("control")

    vivos = mundo.organismos_vivos()

    if modo == "temperatura":
        # El merit crudo de un organismo NUNCA cambia en este modo (nadie
        # resuelve tareas, así que nada lo multiplica) -- se queda fijo
        # en 1.0 para todos, siempre. Lo que de verdad varía con la
        # adaptación de la población es el PESO EFECTIVO que usa el
        # planificador (merit × qué tan bien encaja la temperatura
        # declarada con la actual), que normalmente se calcula al vuelo
        # en Mundo._peso_efectivo y se descarta -- aquí se repite el
        # mismo cálculo solo para poder mostrarlo. Mostrar el merit
        # crudo en la interfaz sería mostrar un número que nunca se
        # mueve, aunque la selección sí esté ocurriendo.
        temperatura_actual = ambiente.temperatura_en(mundo.turno)
        pesos = [
            cpu.merit * factor_temperatura(cpu.temperatura_optima, temperatura_actual, ambiente.ancho_tolerancia)
            for _, _, cpu in vivos
        ]
        metrica_promedio = sum(pesos) / len(pesos) if pesos else 0.0
    else:
        metrica_promedio = sum(cpu.merit for _, _, cpu in vivos) / len(vivos) if vivos else 0.0

    return {
        "modo": modo,
        "categoria_b": "calido" if modo == "temperatura" else "tarea",
        "ancho": mundo.ancho,
        "alto": mundo.alto,
        "celdas": celdas,
        "turno": mundo.turno,
        "poblacion": len(vivos),
        "merit_promedio": round(metrica_promedio, 3),
        "nacimientos": mundo.nacimientos,
        "reemplazos": mundo.reemplazos,
        "temperatura_actual": round(ambiente.temperatura_en(mundo.turno), 1) if modo == "temperatura" else None,
    }


def datos_individuo(cpu: CPU | None, fila: int, columna: int, modo: str) -> dict:
    """Detalle de un solo organismo, para el modal de inspección --
    a diferencia de `serializar()`, esto NO se manda en cada cuadro (sería
    desperdiciar ancho de banda en datos que casi nadie pide todo el
    tiempo); se calcula solo cuando alguien hace clic en una celda.
    """
    if cpu is None:
        return {"tipo": "individuo", "vacio": True, "fila": fila, "columna": columna}

    genoma_legible = [
        f"{instr.opcode} {','.join(str(a) for a in instr.args)}" if instr.args else instr.opcode
        for instr in cpu.genoma
    ]
    datos = {
        "tipo": "individuo",
        "vacio": False,
        "fila": fila,
        "columna": columna,
        "id": cpu.id_organismo,
        "id_padre": cpu.id_padre,
        "generacion": cpu.generacion,
        "merit": round(cpu.merit, 3),
        "longitud_genoma": len(cpu.genoma),
        "genoma": genoma_legible,
    }
    if modo == "temperatura":
        datos["temperatura_optima"] = round(cpu.temperatura_optima, 1) if cpu.temperatura_optima is not None else None
    else:
        datos["tareas_resueltas"] = sorted(cpu.tareas_resueltas)
    return datos


async def receptor(websocket: WebSocket, estado: dict) -> None:
    """Corre en paralelo al bucle principal, escuchando mensajes de
    control del navegador (pausar/reanudar/reiniciar) sin bloquear el
    envío de cuadros."""
    async for mensaje in websocket.iter_text():
        try:
            datos = json.loads(mensaje)
        except json.JSONDecodeError:
            continue
        if not isinstance(datos, dict):
            # Un mensaje bien formado en JSON pero que no es un objeto
            # (ej. `42` o `[1,2]`) no debe tumbar esta tarea -- si eso
            # pasara, esta conexión se quedaría sin poder recibir
            # pausar/reiniciar/cambiar de modo por el resto de la sesión,
            # sin ningún aviso.
            continue
        estado["accion"] = datos.get("accion")
        for campo in ("tasa_mutacion", "temperatura_inicial", "tasa_cambio_temperatura"):
            if campo in datos:
                try:
                    estado[campo] = float(datos[campo])
                except (TypeError, ValueError):
                    pass  # valor no numérico -- se ignora, no se tumba la tarea
        if "modo" in datos and datos["modo"] in ("tarea", "temperatura"):
            estado["modo"] = datos["modo"]
        if "fila" in datos and "columna" in datos:
            try:
                estado["fila"] = int(datos["fila"])
                estado["columna"] = int(datos["columna"])
            except (TypeError, ValueError):
                pass


@router.get("/")
async def index():
    return FileResponse("webapp/static/index.html")


@router.websocket("/ws")
async def simular(websocket: WebSocket):
    global conexiones_activas

    if conexiones_activas >= MAXIMO_CONEXIONES_SIMULTANEAS:
        # Aceptamos primero, a propósito, solo para poder mandar un
        # motivo legible -- cerrar ANTES de aceptar rechaza a nivel del
        # handshake HTTP (403), y el WebSocket nativo del navegador no
        # puede leer ese rechazo como un mensaje específico, solo como
        # una conexión fallida genérica (indistinguible de un error de
        # red). El costo de aceptar y cerrar de inmediato es mínimo.
        await websocket.accept()
        await websocket.send_json({"error": "servidor_lleno"})
        await websocket.close(code=1013)  # 1013 = "try again later"
        return

    await websocket.accept()
    conexiones_activas += 1
    estado = {
        "accion": None,
        "modo": "tarea",
        "tasa_mutacion": 0.0075,
        "temperatura_inicial": -15.0,
        "tasa_cambio_temperatura": 0.0003,
    }
    tarea_receptor = asyncio.create_task(receptor(websocket, estado))

    mundo, ambiente, modo = crear_mundo(estado)
    corriendo = True

    try:
        while True:
            accion = estado.pop("accion", None)
            if accion == "pausar":
                corriendo = False
            elif accion == "reanudar":
                corriendo = True
            elif accion == "reiniciar":
                mundo, ambiente, modo = crear_mundo(estado)
                corriendo = True
            elif accion == "inspeccionar":
                # No cambia `corriendo` ni consume el resto del turno --
                # es una consulta de solo lectura, aparte del ciclo normal
                # de simulación. Validamos los límites por si acaso: un
                # clic en el navegador nunca debería mandar coordenadas
                # fuera de la rejilla, pero nada impide que alguien mande
                # el mensaje a mano por la consola.
                fila = estado.get("fila")
                columna = estado.get("columna")
                if fila is not None and columna is not None and 0 <= fila < mundo.alto and 0 <= columna < mundo.ancho:
                    cpu_inspeccionado = mundo.celdas[fila][columna]
                    await websocket.send_json(datos_individuo(cpu_inspeccionado, fila, columna, modo))

            if corriendo:
                turnos = TURNOS_POR_CUADRO_TEMPERATURA if modo == "temperatura" else TURNOS_POR_CUADRO_TAREA
                mundo.ejecutar_ciclos(turnos, instrucciones_por_turno=3)

            # Un visitante puede cerrar la pestaña justo mientras este
            # bucle está dormido en el `sleep` de abajo -- sin este
            # chequeo, el próximo `send_json` lanza un RuntimeError (no
            # un WebSocketDisconnect) porque uvicorn ya procesó el cierre
            # del lado del cliente. Encontrado probando el límite de
            # conexiones simultáneas con cierres en ráfaga.
            if websocket.client_state != WebSocketState.CONNECTED:
                break

            await websocket.send_json(serializar(mundo, ambiente, modo))
            await asyncio.sleep(INTERVALO_SEGUNDOS)
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        conexiones_activas -= 1
        tarea_receptor.cancel()


app.include_router(router)
