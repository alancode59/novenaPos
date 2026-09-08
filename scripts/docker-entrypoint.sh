#!/bin/sh
# En Render la imagen se construye antes de que exista la base.
set -e

echo "==> Aplicando migraciones pendientes"
flask db upgrade

echo "==> Verificando usuario admin inicial"
python scripts/create_admin.py

# --workers 1 DELIBERADO: el limiter guarda los contadores en memoria.
echo "==> Iniciando gunicorn en el puerto ${PORT:-5000}"
exec gunicorn \
    --bind "0.0.0.0:${PORT:-5000}" \
    --workers 1 \
    --access-logfile - \
    --error-logfile - \
    wsgi:app
