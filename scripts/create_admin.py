"""Crea el primer admin de una instancia. Idempotente: no toca cuentas existentes."""
import os
import sys
from datetime import datetime

from app import create_app
from app.extensions import db
from app.models.user import User
from app.security.hashing import hash_password
from app.security.usernames import normalize_username

LONGITUD_MINIMA = 12


def main() -> int:
    username = normalize_username(os.environ.get("ADMIN_USERNAME"))
    password = os.environ.get("ADMIN_PASSWORD", "")

    if not username or not password:
        print("create_admin: ADMIN_USERNAME/ADMIN_PASSWORD no definidos, no se crea nada.")
        return 0

    if len(password) < LONGITUD_MINIMA:
        print(
            f"create_admin: ERROR - ADMIN_PASSWORD debe tener al menos "
            f"{LONGITUD_MINIMA} caracteres.",
            file=sys.stderr,
        )
        return 1

    app = create_app()
    with app.app_context():
        if db.session.scalar(db.select(User).filter_by(role="admin")):
            print("create_admin: ya existe un admin, no se crea nada.")
            return 0

        if db.session.scalar(db.select(User).filter_by(username=username)):
            print(
                f"create_admin: ERROR - el usuario '{username}' ya existe con "
                f"otro rol; no se toca.",
                file=sys.stderr,
            )
            return 1

        db.session.add(
            User(
                username=username,
                password_hash=hash_password(password),
                role="admin",
                is_active=True,
                must_change_password=True,
                password_changed_at=datetime.utcnow(),
            )
        )
        db.session.commit()
        print(
            f"create_admin: admin '{username}' creado. Debe cambiar la "
            f"contrasena en el primer login."
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
