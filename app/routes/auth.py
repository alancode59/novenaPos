from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_user, logout_user
from werkzeug.exceptions import MethodNotAllowed, NotFound
from werkzeug.routing import RequestRedirect

from app import PUBLIC_ENDPOINTS
from app.auth.decorators import login_required_marked
from app.extensions import db, limiter
from app.models.user import User
from app.security.hashing import hash_password, verify_password
from app.security.usernames import normalize_username

auth_bp = Blueprint("auth", __name__)

# Landing por rol tras un login exitoso.
ROLE_LANDING_ENDPOINTS = {
    "mesero": "orders.tables",
    "cocina": "kitchen.queue",
    "caja": "cashier.pending",
    "admin": "products.dashboard",
}

MIN_PASSWORD_LENGTH = 8

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)

# Expiracion por rol: permanent_session_lifetime es global y no sirve aqui.
ROLE_SESSION_LIFETIME = {
    "admin": timedelta(hours=2),
    "caja": timedelta(minutes=30),
    "mesero": timedelta(hours=8),
    "cocina": timedelta(hours=12),
}
DEFAULT_SESSION_LIFETIME = timedelta(hours=2)


@auth_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "auth", "status": "ok"})


def _is_safe_next_path(target: str) -> bool:
    """Solo rutas relativas del propio sitio (anti open-redirect)."""
    if not target:
        return False
    parsed = urlparse(target)
    return not parsed.netloc and not parsed.scheme and target.startswith("/")


def _landing_url_for_role(role) -> str:
    """URL de aterrizaje segun el rol; rol desconocido -> vista neutra."""
    endpoint = ROLE_LANDING_ENDPOINTS.get(role)
    if endpoint is None:
        current_app.logger.warning("landing sin mapear para role=%r", role)
        return url_for("auth.no_landing")
    return url_for(endpoint)


def _endpoint_allows_role(next_path: str, role) -> bool:
    """True si `role` alcanza el endpoint de `next_path`; ante duda, False."""
    parsed = urlparse(next_path)
    adapter = current_app.url_map.bind(current_app.config.get("SERVER_NAME") or "localhost")
    try:
        endpoint, _values = adapter.match(parsed.path)
    except (NotFound, MethodNotAllowed, RequestRedirect):
        return False

    if endpoint in PUBLIC_ENDPOINTS:
        return True

    view_func = current_app.view_functions.get(endpoint)
    if view_func is None:
        return False

    allowed_roles = getattr(view_func, "_allowed_roles", None)
    if allowed_roles is None:
        # Exige sesion pero no restringe por rol.
        return True
    return role in allowed_roles


def _wants_json() -> bool:
    return request.accept_mimetypes.best_match(["application/json", "text/html"]) == "application/json"


def _generic_login_error():
    """Error de login identico sea cual sea la causa; la real solo va al log."""
    if _wants_json():
        return jsonify({"error": "invalid_credentials"}), 401
    return (
        render_template(
            "auth/login.html",
            error="Usuario o contrasena incorrectos.",
            next=request.form.get("next", ""),
            username=(request.form.get("username") or "").strip(),
        ),
        401,
    )


@auth_bp.route("/login", methods=["GET"])
def login():
    if current_user.is_authenticated:
        if current_user.must_change_password:
            return redirect(url_for("auth.change_password"))
        return redirect(_landing_url_for_role(current_user.role))
    next_url = request.args.get("next", "")
    reason = request.args.get("reason")
    return render_template(
        "auth/login.html", next=next_url, error=None, username="", reason=reason
    )


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login_post():
    username = normalize_username(request.form.get("username"))
    password = request.form.get("password") or ""
    next_url = request.form.get("next", "")

    if not username or not password:
        current_app.logger.info("login rechazado: falta username o password")
        return _generic_login_error()

    user = db.session.execute(
        db.select(User).filter_by(username=username)
    ).scalar_one_or_none()

    if user is None:
        current_app.logger.info("login rechazado: usuario inexistente (%s)", username)
        return _generic_login_error()

    now = datetime.utcnow()

    if user.locked_until is not None and user.locked_until > now:
        current_app.logger.info(
            "login rechazado: cuenta bloqueada username=%s hasta=%s",
            username,
            user.locked_until,
        )
        return _generic_login_error()

    if not user.is_active:
        current_app.logger.info("login rechazado: usuario inactivo username=%s", username)
        return _generic_login_error()

    if not verify_password(user.password_hash, password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = now + LOCKOUT_DURATION
            current_app.logger.info(
                "cuenta bloqueada por intentos fallidos username=%s", username
            )
        db.session.commit()
        current_app.logger.info(
            "login rechazado: password incorrecto username=%s intentos=%s",
            username,
            user.failed_login_attempts,
        )
        return _generic_login_error()

    # Password correcto: reset de contador de intentos fallidos y login.
    user.failed_login_attempts = 0
    user.locked_until = None
    db.session.commit()

    login_user(user)

    lifetime = ROLE_SESSION_LIFETIME.get(user.role, DEFAULT_SESSION_LIFETIME)
    auth_ts = datetime.now(timezone.utc)
    session["auth_ts"] = auth_ts.timestamp()
    session["expires_at"] = (auth_ts + lifetime).timestamp()

    current_app.logger.info("login exitoso username=%s role=%s", username, user.role)

    if user.must_change_password:
        # Prioridad sobre `next`: sin cambiar el password no va a otra pantalla.
        return redirect(url_for("auth.change_password"))

    if _is_safe_next_path(next_url) and _endpoint_allows_role(next_url, user.role):
        return redirect(next_url)
    # `next` de otra area: se ignora en silencio, sin pista de cual era.
    return redirect(_landing_url_for_role(user.role))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required_marked
def change_password():
    """Cambio de password: obligatorio si `must_change_password`, opcional si no."""
    if request.method == "GET":
        return render_template("auth/change_password.html", error=None)

    current_password = request.form.get("current_password") or ""
    new_password = request.form.get("new_password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    def _error(message, status=400):
        return render_template("auth/change_password.html", error=message), status

    if not current_password or not new_password or not confirm_password:
        return _error("Completa todos los campos.")

    if not verify_password(current_user.password_hash, current_password):
        return _error("La contrasena actual es incorrecta.")

    if new_password != confirm_password:
        return _error("La confirmacion no coincide con la nueva contrasena.")

    if len(new_password) < MIN_PASSWORD_LENGTH:
        return _error(
            f"La nueva contrasena debe tener al menos {MIN_PASSWORD_LENGTH} caracteres."
        )

    if verify_password(current_user.password_hash, new_password):
        return _error("La nueva contrasena debe ser distinta de la actual.")

    current_user.password_hash = hash_password(new_password)
    current_user.password_changed_at = datetime.utcnow()
    current_user.must_change_password = False
    db.session.commit()

    current_app.logger.info(
        "password cambiado username=%s", current_user.username
    )

    return redirect(_landing_url_for_role(current_user.role))


@auth_bp.route("/no-landing", methods=["GET"])
@login_required_marked
def no_landing():
    """Fallback para roles sin landing asignado. No expone otras areas."""
    current_app.logger.warning(
        "usuario autenticado sin landing por rol: username=%s role=%r",
        current_user.username,
        current_user.role,
    )
    return "Tu cuenta no tiene un area asignada. Contacta al administrador.", 200


@auth_bp.route("/logout", methods=["POST"])
@login_required_marked
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("auth.login", reason="logout"))
