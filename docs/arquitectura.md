# Arquitectura — proVida

Stack: **Python 3**. Decisiones de diseño tomadas en Fase 2, con su justificación.

## Decisiones de diseño confirmadas

| Decisión | Elegido | Por qué |
|---|---|---|
| Stack tecnológico | Python | Legibilidad pedagógica máxima + mejor ecosistema para Fase 6 (matplotlib, pandas, networkx). Riesgo de rendimiento aceptado para el tamaño de población del MVP. |
| Direccionamiento de saltos | Indexado simple (offsets relativos) | El MVP solo tiene mutación por sustitución (no inserción/deleción), así que el genoma nunca cambia de tamaño — el problema que resuelven los nop-labels de Avida real casi no aplica todavía. Prioriza velocidad de aprendizaje sobre fidelidad total. |
| Topología del mundo | Grid espacial 2D toroidal, vecindario de Moore (8 vecinos) | Fiel al Avida real; permite observar fenómenos espaciales (un genotipo "invadiendo" territorio) que serán muy visibles en la Fase 6. |

## 1. Lenguaje de instrucciones

Set reducido de 15 instrucciones. Nota importante: la **única instrucción lógica es `nand`** — deliberadamente no existen instrucciones `and`, `or`, `not` directas. NAND es funcionalmente completa (cualquier función booleana se puede construir combinando NAND), así que darle solo esa pieza al organismo es lo que obliga a que resolver NOT o AND sea algo que la **evolución tiene que descubrir** combinando instrucciones — si le diéramos AND directo, la tarea "AND" dejaría de ser un logro evolutivo y pasaría a ser trivial. Esto replica fielmente el diseño real de Avida y es el corazón de por qué el sistema produce complejidad interesante.

| Instrucción | Efecto |
|---|---|
| `nop` | No hace nada (relleno) |
| `mov Rd, Rs` | `Rd ← Rs` |
| `inc R` | `R ← R + 1` |
| `dec R` | `R ← R - 1` |
| `add Rd, Rs` | `Rd ← Rd + Rs` |
| `nand Rd, Rs` | `Rd ← NAND(Rd, Rs)` bit a bit — única instrucción lógica |
| `push R` | Apila el valor de `R` |
| `pop R` | Desapila hacia `R` |
| `jmp offset` | Salto relativo incondicional |
| `jmp-if-zero R, offset` | Salto relativo si `R == 0` |
| `input R` | Lee un bit aleatorio del ambiente hacia `R` |
| `output R` | Entrega `R` como salida; el ambiente revisa si resuelve alguna tarea lógica pendiente |
| `h-alloc` | Reserva memoria para el genoma de la cría |
| `h-copy` | Copia la instrucción en `read-head` hacia `write-head` (con probabilidad `p` de mutación), avanza ambos heads |
| `h-divide` | Finaliza la replicación: separa la cría como nuevo organismo y lo coloca en el vecindario del grid |

## 2. Máquina virtual (VM)

Cada organismo tiene su propio estado de VM:

- **Registros:** `AX`, `BX`, `CX` (enteros).
- **Pila:** compartida entre registros, LIFO.
- **Puntero de instrucción (IP):** posición actual de ejecución normal.
- **Read-head / Write-head:** posiciones usadas exclusivamente por `h-copy` durante la auto-replicación — independientes del IP, para que "ejecutarse" y "copiarse" sean procesos conceptualmente paralelos.
- **Merit:** valor numérico que determina la probabilidad de ser elegido por el planificador (ver sección 3).
- **Tareas ya resueltas:** registro de qué tareas lógicas ya premiaron a este organismo (cada tarea se recompensa **una sola vez por organismo**, para que no pueda explotar la recompensa repitiendo el mismo output infinitas veces).
- **Últimos inputs recibidos:** necesarios para que `output` pueda verificarse contra las tareas lógicas (NOT necesita el último input; AND/NAND necesitan los dos últimos).

## 3. Motor de mundo / población

- **Grid 2D toroidal** de tamaño configurable (ej. 20×20 = 400 celdas máximo). Toroidal = los bordes se conectan (como un mapa que da la vuelta), para que no haya organismos "en el borde" con menos vecinos — evita un sesgo artificial de selección solo por posición geométrica.
- **Planificador ponderado por merit:** en cada "time slice" global, se sortea qué organismo ejecuta su siguiente bloque de instrucciones, con probabilidad proporcional a su merit relativo dentro de la población completa. No hay tiempo real ni concurrencia — es un bucle síncrono con sorteo ponderado.
- **Reemplazo por vecindario (Moore, 8 vecinos):** cuando un organismo ejecuta `h-divide`, la cría se coloca en una celda del vecindario de 8 posiciones alrededor del padre. Si esa celda está ocupada, el organismo que estaba ahí es reemplazado (muere). Esto es lo que produce competencia espacial local: los genotipos exitosos forman "manchas" que se expanden gradualmente, en vez de invadir instantáneamente todo el grid.

## 4. Sistema de mutación

- **Tipo:** solo sustitución en el MVP (una instrucción copiada se reemplaza por una instrucción aleatoria del set completo).
- **Momento:** ocurre exclusivamente durante `h-copy`, instrucción por instrucción.
- **Tasa por defecto:** 0.75% por instrucción copiada (valor clásico de Avida), expuesta como parámetro configurable del motor — no hardcodeada — para poder experimentar con presión mutacional más adelante (Fase 7).

## 5. Sistema de recompensa por tareas lógicas

Tareas del MVP (subconjunto pequeño, en orden de dificultad creciente):

1. **NOT** — `output == NOT(último input)`
2. **AND** — `output == AND(input[-2], input[-1])`
3. **NAND** — `output == NAND(input[-2], input[-1])` (nota: esta es "gratis" en cierto sentido porque coincide con la instrucción primitiva, pero el organismo igual tiene que orquestar `input`/`output` correctamente para reclamarla)

Cuando el ambiente detecta que un `output` resuelve una tarea no reclamada antes por ese organismo, incrementa su **merit**. Un merit más alto no ejecuta "más rápido" de forma determinista — aumenta la *probabilidad* de ser elegido por el planificador ponderado (sección 3), lo cual en promedio, sobre muchas rondas, se traduce en más réplicas. Esto es exactamente el mecanismo por el cual "resolver una tarea" se convierte en "dejar más descendencia" sin que el código declare un fitness explícito en ningún lado — el fitness es una consecuencia observada, no una variable que el sistema asigna directamente.

## 6. Diagrama de arquitectura

```mermaid
flowchart TB
    subgraph Mundo["Mundo: grid 2D toroidal"]
        Scheduler["Planificador\n(sorteo ponderado por merit)"]
        subgraph Grid["Celdas del grid (organismos)"]
            OrgA["Organismo A\n(VM: genoma, registros,\nheads, pila, merit)"]
            OrgB["Organismo B"]
            OrgVecino["... vecinos Moore (8)"]
        end
    end

    Scheduler -->|"elige organismo,\nejecuta N instrucciones"| OrgA
    OrgA -->|"input / output"| Ambiente["Ambiente\n(fuente de bits +\nverificador de tareas lógicas)"]
    Ambiente -->|"otorga merit\npor tarea resuelta"| OrgA
    OrgA -->|"h-copy"| Mutacion["Módulo de mutación\n(sustitución, prob. p)"]
    OrgA -->|"h-divide\n(coloca cría en vecindario)"| Grid
    OrgA -.->|"eventos: nacimiento,\ntarea resuelta, muerte"| Metricas["Registro de métricas"]
    Metricas -.-> Fase6["Fase 6:\nvisualización y análisis"]
```

## 7. Estructura de módulos prevista (referencia para Fase 3)

```
provida/
  vm/            # instrucciones, VM individual, ejecución de un organismo
  world/         # grid, planificador, colocación/reemplazo de organismos
  mutation/      # lógica de sustitución durante h-copy
  tasks/         # definición y verificación de tareas lógicas
  metrics/       # registro de eventos para la Fase 6
  cli.py         # punto de entrada para correr simulaciones desde terminal
tests/
docs/
```

Esta estructura es orientativa — se ajustará en la Fase 3 cuando se inicialice el repo real.
