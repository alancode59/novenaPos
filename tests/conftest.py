import os

# Deben existir ANTES de importar `app`: Config lee SECRET_KEY al importarse.
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("PASSWORD_PEPPER", "test-pepper-not-for-production")
os.environ.setdefault("FORCE_INSECURE_COOKIES", "1")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://posnovena:posnovena@127.0.0.1:5433/posnovena_test"
)

import pytest
from sqlalchemy.engine import make_url

from app import create_app
from app.extensions import db
from app.models.user import User
from app.security.hashing import hash_password


def _assert_database_is_disposable(uri):
    # Las fixtures hacen drop_all(): apuntar a la base de dev la borra.
    url = make_url(uri)
    name = url.database or ""

    if url.get_backend_name() == "sqlite" and name in ("", ":memory:"):
        return
    if name.endswith("_test"):
        return

    pytest.exit(
        f"Los tests apuntan a la base '{name}', que no es descartable.\n"
        f"Las fixtures ejecutan drop_all() y borrarian sus datos.\n"
        f"Use una base cuyo nombre termine en '_test', por ejemplo:\n"
        f"  DATABASE_URL=postgresql+psycopg://posnovena:posnovena@127.0.0.1:5433/posnovena_test",
        returncode=1,
    )


@pytest.fixture
def app():
    app = create_app()
    app.config.update({"TESTING": True, "WTF_CSRF_ENABLED": False})
    _assert_database_is_disposable(app.config["SQLALCHEMY_DATABASE_URI"])
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        # Sin dispose, las conexiones chocan con el DROP/CREATE del siguiente test.
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(app):
    """Factory para crear usuarios de prueba con password conocido."""

    def _make_user(username="mesero1", password="Sup3rSecreta!", role="mesero", is_active=True):
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            is_active=is_active,
        )
        db.session.add(user)
        db.session.commit()
        return user

    return _make_user
