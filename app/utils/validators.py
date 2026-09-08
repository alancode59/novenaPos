def require_fields(payload: dict, fields: list[str]) -> list[str]:
    """Regresa la lista de campos faltantes en el payload."""
    return [f for f in fields if f not in payload or payload[f] in (None, "")]
