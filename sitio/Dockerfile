# Build multi-etapa: la primera etapa corre las simulaciones y genera el
# sitio estático (HTML + PNG); la segunda solo sirve esos archivos con
# Nginx. Así el contenedor final no lleva Python ni las dependencias de
# análisis (matplotlib/pandas/networkx) -- solo HTML/CSS/imágenes, igual
# que cualquier otro sitio estático del portafolio.

FROM python:3.12-slim AS build
WORKDIR /app
COPY pyproject.toml README.md ./
COPY provida/ provida/
COPY sitio/ sitio/
RUN pip install --no-cache-dir -e ".[analisis]"
RUN python3 sitio/generar.py

FROM nginx:alpine
COPY --from=build /app/sitio/build /usr/share/nginx/html
EXPOSE 80
