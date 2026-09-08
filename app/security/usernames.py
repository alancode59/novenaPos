"""Normalizacion de nombres de usuario."""


def normalize_username(valor) -> str:
    # Postgres distingue mayusculas: `Admin` y `admin` serian cuentas distintas.
    if not valor:
        return ""
    return valor.strip().lower()
