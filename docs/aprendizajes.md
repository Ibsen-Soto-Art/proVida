# Aprendizajes — proVida

Checklist de lo que este proyecto dejó como evidencia de aprendizaje, con el artefacto concreto (código, prueba o documento) que lo respalda. Organizado por área, no por fase — muchos aprendizajes cruzan varias fases.

## Biología evolutiva, hecha ejecutable

- [x] **Replicación con herencia y variación heredable es suficiente para que haya selección natural** — no hace falta que nadie declare un "fitness" explícito. Evidencia: [`tests/test_seleccion_natural.py`](../tests/test_seleccion_natural.py), donde el genotipo con tarea pasa de 50% a 100% de la población sin que ningún código lo fuerce.
- [x] **"Generación" no es un contador de tiempo sincronizado** en poblaciones con reproducción asíncrona y solapada (como bacterias en cultivo continuo) — es más útil como profundidad de linaje. Evidencia: [`docs/glosario.md`](glosario.md) y el hallazgo de que la generación máxima en 60 000 turnos fue solo 14, no cientos, documentado en [`docs/observabilidad.md`](observabilidad.md).
- [x] **La exclusión competitiva puede ser total, no gradual**: con ventaja reproductiva sostenida, un genotipo puede desplazar a otro por completo en vez de coexistir en proporciones estables — el mismo patrón que en ecología de poblaciones real.
- [x] **NAND como única instrucción lógica obliga a que combinar operaciones sea un logro evolutivo real**, no una casilla que se marca sola — entendí de primera mano por qué Avida diseñó su set de instrucciones así (ver `docs/arquitectura.md`, sección 1).
- [x] **Un mecanismo simple (competencia por turnos de CPU) produce una curva de crecimiento logística sin que nadie programe un límite de capacidad** — la misma forma que en ecología de poblaciones con recursos limitados (ver `examples/demo_poblacion.py`).

## Diseño de sistemas y teoría de la computación

- [x] **Diseñar una máquina virtual desde cero**: registros, pila, punteros de instrucción, y la diferencia entre "ejecutarse" y "copiarse" como procesos paralelos (IP vs. read/write-heads).
- [x] **Direccionamiento indexado vs. por contenido (nop-labels) es un trade-off real, no una curiosidad histórica** — lo viví en carne propia: elegí indexado en la Fase 2 por simplicidad, y en la Fase 7 tuve que resolver a mano el problema exacto que los nop-labels evitan (un genoma no puede conocer su propio tamaño usando solo `inc`, porque el contador ocupa instrucciones que también hay que contar).
- [x] **Un diseño puede volverse obsoleto conforme el sistema crece, y hay que revisarlo con evidencia, no por capricho** — pasó tres veces: `h-copy` sin `h-alloc` (de excepción a no-op, Fase 4), `h-divide` con copia incompleta (de "falla" a "completa con cría truncada", Fase 7), y el valor congelado de una prueba de regresión (cambió porque el set de instrucciones creció, no por un bug).
- [x] **Los sistemas probabilísticos necesitan una estrategia de testing distinta a la de un CRUD**: determinista puro, estadística con tolerancia, emergente con control nulo, y regresión con semillas fijas — cuatro técnicas distintas para cuatro tipos de comportamiento (ver `docs/testing.md`).
- [x] **Inyectar el generador aleatorio (`random.Random`) en vez de usar el global es lo que hace posible la reproducibilidad** — sin esto, ninguna prueba de regresión habría sido viable.

## Proceso de trabajo

- [x] **Explicar el "por qué" antes de escribir código cambia las decisiones que se toman** — varias veces el razonamiento biológico llevó a una decisión de diseño distinta a la que habría tomado por puro instinto de programador (ej. bonos multiplicativos en vez de aditivos por tarea, para que resolver varias tareas componga la ventaja en vez de sumarla linealmente).
- [x] **Verificar visualmente antes de decir "funciona"** — varias demos con gráficas se revisaron leyendo la imagen generada, no solo confirmando que el script corría sin error; eso encontró al menos un caso donde el resultado esperado no coincidía con el real y había que ajustar parámetros (los puntos de control de turnos en `demo_poblacion.py` y `demo_seleccion_natural.py`).
- [x] **Un hallazgo inesperado vale más documentarlo que ocultarlo** — el 32% de organismos degenerados de una instrucción en el experimento de indels (Fase 7) no se buscó ni se explicó del todo, y quedó documentado como pregunta abierta en vez de forzarlo a encajar en la narrativa esperada.

## Lo que quedó fuera (a propósito)

Documentado en [`docs/vision-tecnica.md`](vision-tecnica.md) desde la Fase 0: árbol filogenético completo, ambientes con recursos limitados, coevolución hospedero-parásito, y el catálogo completo de tareas lógicas de Avida (hasta EQU) — quedaron fuera del alcance de este MVP+extensión, no por falta de interés sino por decisión consciente de scope frente al tiempo disponible antes de la etapa productiva.
