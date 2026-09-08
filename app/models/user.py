import sqlalchemy as sa
from flask_login import UserMixin

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, mesero, cocina, caja

    # Columna, no la property de UserMixin; cubierto por test.
    is_active = db.Column(db.Boolean, default=True)

    # Fuerza bruta / bloqueo de cuenta.
    failed_login_attempts = db.Column(
        db.Integer, nullable=False, default=0, server_default=sa.text("0")
    )
    locked_until = db.Column(db.DateTime, nullable=True)

    # Higiene de contrasenas.
    password_changed_at = db.Column(db.DateTime, nullable=True)
    must_change_password = db.Column(
        db.Boolean, nullable=False, default=False, server_default=sa.text("false")
    )

    def __repr__(self):  # pragma: no cover
        return f"<User {self.username!r} role={self.role!r}>"
