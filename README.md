# proVida

Simulador de vida digital inspirado en [Avida](https://en.wikipedia.org/wiki/Avida) (Ofria, Adami, Pennock — Michigan State University), construido desde cero como proyecto de aprendizaje.

Organismos digitales — programas autorreplicantes que corren sobre una máquina virtual propia — compiten por espacio y tiempo de CPU en un mundo simulado. Mutan al copiarse, y los que resuelven tareas lógicas obtienen más ciclos de ejecución, lo que se traduce en más descendencia. La selección natural y la evolución de complejidad emergen de estas reglas simples, sin que el sistema optimice nada de forma explícita.

## Estado del proyecto

En desarrollo activo. Ver [docs/](docs/) para la documentación completa de diseño.

## Documentación

- [Visión técnica](docs/vision-tecnica.md) — problema, objetivo de aprendizaje, alcance del MVP.
- [Glosario](docs/glosario.md) — términos técnicos con su analogía biológica.
- [Arquitectura](docs/arquitectura.md) — diseño de la VM, el lenguaje de instrucciones, el motor de mundo/población, mutación y tareas lógicas.

## Stack

Python 3.11+.

## Desarrollo

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Licencia

Proyecto personal de aprendizaje / portafolio.
