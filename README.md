# posNovena — SaaS POS para pizzerías

Stack: **Flask + MySQL + Docker + Tailwind CSS**. Instancia dedicada por cliente.

Roles: `admin`, `mesero`, `cocina`, `caja`.

## Desarrollo local

    cp .env.example .env
    docker compose up --build

La app queda en http://localhost:5000 (phpMyAdmin en :8080).

### El CSS hay que compilarlo

`app/static/css/output.css` es un artefacto y **no está en el repo** (ver
`.gitignore`). El contenedor lo hornea al construir la imagen, pero en
desarrollo `docker-compose` monta `.:/app` encima, así que se usa el del
host. Si la app se ve sin estilos, es esto:

    npm install
    npm run build:css     # o `npm run watch:css` mientras editas plantillas

Tailwind purga por contenido: una clase nueva en una plantilla no existe
en `output.css` hasta que recompilas.

### Primer usuario

Una base recién creada no tiene usuarios (`scripts/seed_db.py` solo
siembra productos). Para crear el admin inicial:

    PYTHONPATH=. ADMIN_USERNAME=admin ADMIN_PASSWORD='una-clave-larga' python scripts/create_admin.py

El `PYTHONPATH=.` hace falta al correrlo desde el host; dentro del
contenedor ya viene puesto. Lo mismo aplica a `scripts/seed_db.py`.

Se crea con `must_change_password=True`: esa clave solo sirve para el
primer login.

## Tests

    pytest

Corren contra una base aparte. `tests/conftest.py` **aborta la suite** si
`DATABASE_URL` no apunta a una base cuyo nombre termine en `_test`: las
fixtures hacen `drop_all()` y apuntar a la base de desarrollo la borra.

## Despliegue (Render)

`render.yaml` define el servicio. Estas variables se cargan en el
dashboard de Render (`sync: false` = no viajan en el repo):

| Variable | Obligatoria | Notas |
|---|---|---|
| `SECRET_KEY` | Sí | Firma la sesión. Si falta, la app **no arranca** (fail-fast). Generar con `python -c "import secrets; print(secrets.token_hex(32))"`. Rotarla cierra todas las sesiones activas. |
| `PASSWORD_PEPPER` | Sí | Secreto aplicado por HMAC antes de Argon2id. Si falta, `app/security/hashing.py` cae a un fallback que está **en el código fuente**, anulando la protección. |
| `DATABASE_URL` | Sí | MySQL. El default apunta al host `mysql` de docker-compose, que no existe en Render. |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Primer deploy | Crean el admin inicial una sola vez. |
| `FLASK_ENV` | — | `production`. |

El arranque (`scripts/docker-entrypoint.sh`) aplica migraciones, crea el
admin si no existe, y lanza gunicorn.

**gunicorn corre con `--workers 1` a propósito.** Flask-Limiter usa
storage en memoria; con varios workers cada proceso llevaría su propio
contador y el rate limit del login dejaría de ser efectivo. Para escalar
hay que migrar el limiter a Redis primero.
