# Glosario — proVida

Términos técnicos del simulador, cada uno con su analogía biológica correspondiente. Pensado para que la traducción de concepto biológico → concepto computacional (y viceversa) sea explícita.

---

**Organismo**
Instancia individual dentro de la simulación: un genoma + el estado de su máquina virtual (registros, pila, punteros) en un momento dado.
*Analogía biológica:* un individuo — una célula o un virus concreto, no la especie.

**Genoma**
Secuencia ordenada de instrucciones que define a un organismo. Es a la vez el "programa" que se ejecuta y el "dato" que se copia durante la replicación.
*Analogía biológica:* la secuencia de ADN/ARN de un individuo.

**Instrucción**
Unidad mínima ejecutable del genoma (equivalente a un opcode de assembly). Ejemplos que definiremos en Fase 2: sumar registros, saltar, leer un input, escribir en la copia hija.
*Analogía biológica:* aproximable a un codón — una unidad discreta que la maquinaria interpreta como una acción concreta.

**Máquina virtual (VM)**
El "hardware simulado" que interpreta y ejecuta las instrucciones del genoma de un organismo: tiene registros, pila, puntero de instrucción y cabezas de lectura/escritura.
*Analogía biológica:* la maquinaria celular que traduce/ejecuta la información genética (ribosoma + enzimas asociadas), aunque en proVida esta maquinaria es genérica y compartida por todos los organismos, mientras que el "programa" que corre en ella es específico de cada uno.

**Puntero de instrucción (IP)**
Posición dentro del genoma que indica cuál instrucción se ejecuta a continuación. Avanza normalmente en secuencia, salvo que una instrucción de salto lo mueva.
*Analogía biológica:* la posición de la polimerasa sobre el molde en un momento dado.

**Cabezas (heads)**
Punteros adicionales sobre el genoma usados específicamente durante la auto-replicación: típicamente una cabeza de lectura (de dónde se copia) y una de escritura (a dónde se copia). Son independientes del IP.
*Analogía biológica:* el punto de lectura del molde y el punto de síntesis de la nueva hebra durante la replicación del ADN — no son el mismo punto que "qué gen se está expresando ahora mismo".

**Pila (stack)**
Estructura de memoria temporal donde la VM guarda valores intermedios durante operaciones (por ejemplo, al calcular el resultado de una tarea lógica).
*Analogía biológica:* sin equivalente biológico directo — es un mecanismo computacional interno de la maquinaria, no del organismo en sí.

**Registro**
Espacio de memoria pequeño y de acceso rápido dentro de la VM, usado para guardar valores con los que operan las instrucciones.
*Analogía biológica:* aproximable a un cofactor o metabolito intermedio que una enzima usa activamente, aunque es una analogía imperfecta — de nuevo, mecanismo de la maquinaria más que del genoma.

**Auto-replicación**
Proceso por el cual un organismo ejecuta instrucciones de su propio genoma para producir una copia de sí mismo en un nuevo espacio de memoria de la población.
*Analogía biológica:* la replicación del material genético previa a la división celular (o, en un virus de ARN, la síntesis de una nueva hebra usando la propia como molde).

**Mutación (por copia)**
Alteración de una instrucción durante el proceso de copia, con cierta probabilidad (tasa de mutación). En el MVP: sustitución de una instrucción por otra al azar del set disponible.
*Analogía biológica:* error de la polimerasa durante la replicación, no corregido por mecanismos de reparación (las polimerasas sin "proofreading", como muchas ARN-polimerasas virales, tienen tasas de mutación altas).

**Población**
Conjunto de organismos coexistiendo en el "mundo" de la simulación, con un tamaño máximo fijo.
*Analogía biológica:* una población biológica dentro de un hábitat con capacidad de carga limitada.

**Mundo / hábitat**
Estructura (grid o lista) que contiene las posiciones donde pueden existir organismos, con capacidad finita.
*Analogía biológica:* el hábitat físico con recursos y espacio limitados.

**Generación**
No es un contador global sincronizado (los organismos no se replican todos a la vez) — es más útil pensarla como una medida derivada: cuántas replicaciones ha habido en promedio, o el número de "ancestros" entre un organismo y el fundador original de su linaje.
*Analogía biológica:* generación en poblaciones con reproducción asincrónica y solapada (como bacterias en un cultivo continuo), no en poblaciones con generaciones discretas y sincronizadas.

**Merit (mérito)**
Valor numérico asignado a un organismo que determina cuántos ciclos de CPU recibe por unidad de tiempo simulado, en relación al resto de la población. Aumenta al resolver tareas lógicas.
*Analogía biológica:* eficiencia metabólica — cuánta energía utilizable produce el organismo a partir de su ambiente, lo cual determina indirectamente qué tan rápido puede crecer y replicarse.

**Tarea lógica**
Operación booleana (NOT, AND, NAND, etc.) que un organismo puede "resolver" tomando inputs binarios proporcionados por el entorno de simulación y produciendo el output correcto mediante sus instrucciones.
*Analogía biológica:* una vía metabólica capaz de transformar un sustrato ambiental en un producto útil — resolverla con éxito es como tener la enzima adecuada para metabolizar un recurso disponible.

**Fitness**
Éxito reproductivo relativo de un organismo (o de un genotipo) dentro de la población: no es un número que el sistema calcule y asigne directamente, sino una consecuencia emergente de cuánto merit tiene un organismo (qué tan rápido se replica) y cuánto sobrevive antes de ser reemplazado por otra cría.
*Analogía biológica:* fitness darwiniano — éxito reproductivo diferencial, no una propiedad intrínseca fija del organismo sino algo que depende del contexto (ambiente + competencia).

**Selección natural**
Fenómeno emergente por el cual, dada variación heredable (mutación) y éxito reproductivo diferencial (fitness) bajo recursos limitados (espacio en la población), las variantes con mayor fitness tienden a representar una proporción creciente de la población con el tiempo.
*Analogía biológica:* es literalmente el mecanismo darwiniano, aplicado sobre organismos digitales en vez de biológicos.

**Genotipo**
La secuencia exacta de instrucciones de un genoma, usada para agrupar organismos idénticos o para comparar linajes.
*Analogía biológica:* genotipo en el sentido clásico — la secuencia genética, en contraste con el fenotipo (el comportamiento resultante).

**Fenotipo (en este contexto)**
El comportamiento observable de un organismo al ejecutarse: qué tareas lógicas resuelve, cuánto tarda en replicarse, cuántas instrucciones ejecuta antes de morir o replicarse.
*Analogía biológica:* fenotipo — el resultado observable de "correr" el genotipo en un ambiente dado.

**Linaje**
Cadena de organismos relacionados por descendencia directa (padre → hijo → nieto...).
*Analogía biológica:* linaje evolutivo / línea de descendencia.
