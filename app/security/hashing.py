"""Hashing de contrasenas con Argon2id + pepper (HMAC-SHA256)."""
import hashlib
import hmac
import os

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError

# Fallback solo para desarrollo local; en produccion exportar el real.
_DEV_ONLY_PEPPER_FALLBACK = "dev-only-insecure-pepper-CHANGE-ME"

_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=19456,
    parallelism=1,
    hash_len=32,
    salt_len=16,
)


def _get_pepper() -> bytes:
    pepper = os.environ.get("PASSWORD_PEPPER", _DEV_ONLY_PEPPER_FALLBACK)
    return pepper.encode("utf-8")


def _apply_pepper(plain: str) -> str:
    """Aplica HMAC-SHA256(pepper, plain) y regresa el digest en hex."""
    mac = hmac.new(_get_pepper(), plain.encode("utf-8"), hashlib.sha256)
    return mac.hexdigest()


def hash_password(plain: str) -> str:
    """Genera un hash Argon2id del password, aplicando pepper primero."""
    peppered = _apply_pepper(plain)
    return _password_hasher.hash(peppered)


def verify_password(stored_hash: str, plain: str) -> bool:
    """Verifica un password; cualquier fallo devuelve False, nunca excepcion."""
    if not stored_hash or not plain:
        return False
    peppered = _apply_pepper(plain)
    try:
        _password_hasher.verify(stored_hash, peppered)
        return True
    except (VerifyMismatchError, InvalidHash):
        return False
    except Exception:
        # Defensa en profundidad: ningun error de la libreria llega al caller.
        return False
