import os


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _normalize_db_uri(uri: str) -> str:
    # Render entrega `postgres://`, que SQLAlchemy 2 ya no acepta.
    if uri.startswith("postgres://"):
        return "postgresql+psycopg://" + uri[len("postgres://"):]
    if uri.startswith("postgresql://"):
        return "postgresql+psycopg://" + uri[len("postgresql://"):]
    return uri


class Config:
    # Fail-fast: sin SECRET_KEY la app no arranca.
    SECRET_KEY = os.environ["SECRET_KEY"]

    SQLALCHEMY_DATABASE_URI = _normalize_db_uri(
        os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://posnovena:posnovena@db:5432/posnovena",
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Pepper de contrasenas; ver app/security/hashing.py.
    PASSWORD_PEPPER = os.environ.get("PASSWORD_PEPPER")

    # Secure siempre: atarlo a FLASK_ENV permitiria olvidarlo en produccion.
    SESSION_COOKIE_SECURE = not _env_flag("FORCE_INSECURE_COOKIES")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_NAME = "posnovena_session"
    SESSION_REFRESH_EACH_REQUEST = True
