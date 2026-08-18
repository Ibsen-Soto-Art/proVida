# A diferencia de sitio/Dockerfile (build multi-etapa que descarta Python
# al final), esta imagen SÍ necesita Python corriendo permanentemente --
# cada visitante mantiene una simulación viva en el servidor mientras
# tenga la página abierta, no es contenido generado una sola vez.

FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY provida/ provida/
COPY webapp/ webapp/
RUN pip install --no-cache-dir -e ".[web]"

EXPOSE 80
CMD ["uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "80"]
