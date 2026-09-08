# Etapa 1: compilar el CSS; output.css no viaja en el repo.
FROM node:20-slim AS css

WORKDIR /build

COPY package.json package-lock.json ./
RUN npm ci

# Tailwind purga por contenido: necesita ver plantillas y JS reales.
COPY tailwind.config.js ./
COPY app/static/css/input.css ./app/static/css/input.css
COPY app/templates ./app/templates
COPY app/static/js ./app/static/js

RUN npm run build:css


# Etapa 2: runtime
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=wsgi.py \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=css /build/app/static/css/output.css ./app/static/css/output.css

# chmod explicito: en Windows el bit de ejecucion no sobrevive a git.
RUN chmod +x ./scripts/docker-entrypoint.sh

# El proceso no debe correr como root (hallazgo de seguridad).
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

CMD ["./scripts/docker-entrypoint.sh"]
