"""Proteccion por rol: sin sesion -> 401/redirect, rol incorrecto -> 403."""
from functools import wraps

from flask import abort, jsonify, redirect, request, url_for
from flask_login import current_user
from flask_login import login_required as _flask_login_required


def wants_json_response() -> bool:
    """True para clientes fetch/AJAX; False para navegacion normal."""
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    if best == "application/json":
        return True
    if request.is_json:
        return True
    return False


def _unauthenticated_response():
    if wants_json_response():
        return jsonify({"error": "authentication_required"}), 401
    return redirect(url_for("auth.login", next=request.path))


def roles_required(*roles):
    """Exige autenticacion y que `current_user.role` este en `roles`."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return _unauthenticated_response()
            if current_user.role not in roles:
                abort(403)
            return view_func(*args, **kwargs)

        wrapped._role_protected = True
        # Permite validar `next` sin duplicar la matriz de roles.
        wrapped._allowed_roles = frozenset(roles)
        return wrapped

    return decorator


def login_required_marked(view_func):
    """`login_required` + marca `_role_protected`, para rutas sin rol especifico."""

    @wraps(view_func)
    @_flask_login_required
    def wrapped(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapped._role_protected = True
    return wrapped
