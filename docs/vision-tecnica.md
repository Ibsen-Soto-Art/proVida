# Documento de Visión Técnica — proVida

## 1. Problema / motivación

¿Cómo emerge la selección natural y la complejidad biológica a partir de reglas simples de replicación, variación y competencia por recursos? La biología evolutiva estudia este fenómeno en organismos reales, donde los tiempos generacionales (días, años, milenios) y la imposibilidad de "rebobinar" la historia hacen muy difícil observar la evolución en acción con el detalle que uno quisiera.

Avida (Ofria, Adami, Pennock — Michigan State University) resolvió esto creando un medio alternativo para la evolución: organismos que son programas de computadora autorreplicantes, ejecutándose en una máquina virtual, compitiendo por tiempo de CPU y espacio en memoria. Al ser digital, cada generación toma microsegundos y cada mutación queda registrada exactamente — se puede observar la evolución completa, no inferirla de fósiles.

**proVida** es una reconstrucción propia, simplificada, de este principio, con fines de aprendizaje profundo (no de investigación).

## 2. Objetivo de aprendizaje

El objetivo de este proyecto no es producir un simulador competitivo con Avida, sino que quien lo construye (Ibsen) entienda de primera mano, implementándolos, los siguientes principios:

- Cómo se diseña una máquina virtual mínima con su propio set de instrucciones.
- Cómo un programa puede tratarse a sí mismo como dato y copiarse instrucción por instrucción (auto-replicación).
- Cómo la mutación durante la copia introduce variación heredable.
- Cómo la competencia por un recurso finito (espacio en la población, tiempo de CPU) convierte la variación en selección natural, sin que el sistema optimice nada explícitamente — el fitness **emerge**, no se declara.
- Cómo diseñar un sistema de recompensa ("tareas lógicas") que actúa como metabolismo simplificado y crea presión selectiva dirigida.
- Cómo instrumentar un sistema evolutivo para poder *observar* estos fenómenos (métricas, visualización), no solo confiar en que "están pasando".

Es, en el fondo, un proyecto de arquitectura de software y de teoría de la computación disfrazado de proyecto de biología — y viceversa.

## 3. Alcance del MVP (decidido en Fase 0)

**Nivel: Intermedio.** El MVP incluye:

- Máquina virtual con registros, puntero de instrucción (IP), pila, y las cabezas de lectura/escritura/flujo necesarias para que un organismo pueda copiarse a sí mismo.
- Un set reducido de instrucciones tipo "assembly" propio (a definir en Fase 2).
- Auto-replicación: un organismo ejecuta instrucciones de su propio genoma para producir una copia de sí mismo en un nuevo espacio de memoria.
- Mutación por copia (sustitución de instrucciones) con tasa configurable.
- Una población de organismos conviviendo en un mundo de tamaño fijo (grid o lista, a definir en Fase 2), compitiendo por espacio: cuando la población está llena, una cría reemplaza a otro organismo existente.
- Tareas lógicas (empezando por un subconjunto pequeño: NOT, AND, NAND) que, al ser resueltas por un organismo usando inputs binarios del ambiente, otorgan recompensa metabólica ("merit") en forma de más ciclos de CPU.
- Verificación observable de selección natural emergente: organismos que resuelven tareas se propagan más que los que no, sin que el código lo fuerce directamente — debe ser una consecuencia del diseño, no una regla explícita tipo "si tarea == true, fitness += 1".

## 4. Qué NO incluye el MVP

Explícitamente fuera de alcance (candidatas para Fase 7 — extensiones):

- Árbol filogenético con seguimiento fino de linajes (más allá de un registro básico de "quién es hijo de quién" para depuración).
- Ambiente con recursos limitados por tipo de tarea (nichos, agotamiento/regeneración de recursos).
- Coevolución hospedero-parásito.
- Presión de selección variable en el tiempo (ambientes cambiantes).
- Todo el catálogo completo de tareas lógicas de Avida real (EQU y combinaciones complejas) — el MVP usa un subconjunto pequeño.
- Interfaz gráfica interactiva en tiempo real (el MVP puede generar visualizaciones a partir de datos registrados, no necesariamente una UI en vivo — esto se decide en Fase 6).
- Optimización de rendimiento para poblaciones grandes (miles de organismos) — el MVP prioriza claridad conceptual sobre escala.

## 5. Público / uso

Proyecto de portafolio y aprendizaje personal. Documentado en español, con comentarios pedagógicos en el código, pensado para poder explicarlo en una entrevista técnica y para servir de evidencia de aprendizaje en la etapa productiva del SENA (ADSO).
