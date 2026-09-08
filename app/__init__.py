from datetime import datetime, timezone

from flask import Flask, g, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, logout_user

from app.auth.decorators import wants_json_response
from app.config import Config
from app.extensions import init_auth, init_db

# Rutas sin autenticacion; todo lo demas exige sesion por defecto.
PUBLIC_ENDPOINTS = {
    "static",
    "auth.login",
    "auth.login_post",
    "auth.health",
    "orders.health",
    "kitchen.health",
    "cashier.health",
    "products.health",
    "inventory.health",
}

# Unicas rutas servibles mientras `must_change_password` sigue activo.
MUST_CHANGE_PASSWORD_ALLOWED_ENDPOINTS = {
    "auth.change_password",
    "auth.logout",
}


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    init_db(app)
    init_auth(app)

    from app import models

    from app.routes.auth import auth_bp
    from app.routes.orders import orders_bp
    from app.routes.kitchen import kitchen_bp
    from app.routes.cashier import cashier_bp
    from app.routes.products import products_bp
    from app.routes.inventory import inventory_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(orders_bp, url_prefix="/orders")
    app.register_blueprint(kitchen_bp, url_prefix="/kitchen")
    app.register_blueprint(cashier_bp, url_prefix="/cashier")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")

    @app.before_request
    def _enforce_session_expiration():
        """Expira la sesion por rol y marca `g.session_expired` para el redirect."""
        if current_user.is_authenticated:
            expires_at = session.get("expires_at")
            if expires_at is None or datetime.now(timezone.utc).timestamp() > expires_at:
                logout_user()
                session.clear()
                g.session_expired = True

    @app.before_request
    def _require_authentication_by_default():
        """Default seguro: todo endpoint fuera de PUBLIC_ENDPOINTS exige sesion."""
        endpoint = request.endpoint
        if endpoint is None or endpoint in PUBLIC_ENDPOINTS:
            return None
        if not current_user.is_authenticated:
            if wants_json_response():
                return jsonify({"error": "authentication_required"}), 401
            login_kwargs = {"next": request.path}
            if getattr(g, "session_expired", False):
                login_kwargs["reason"] = "expired"
            return redirect(url_for("auth.login", **login_kwargs))
        return None

    @app.before_request
    def _enforce_must_change_password():
        # Sin esto bastaria teclear otra URL para saltarse el flujo.
        if not current_user.is_authenticated:
            return None
        if not getattr(current_user, "must_change_password", False):
            return None
        endpoint = request.endpoint
        if endpoint is None:
            return None
        if endpoint in PUBLIC_ENDPOINTS or endpoint in MUST_CHANGE_PASSWORD_ALLOWED_ENDPOINTS:
            return None
        if wants_json_response():
            return jsonify({"error": "password_change_required"}), 403
        return redirect(url_for("auth.change_password"))

    @app.errorhandler(429)
    def _rate_limit_exceeded(error):
        # Limite por IP, no por cuenta: no revela si un usuario existe.
        if wants_json_response():
            return jsonify({"error": "rate_limit_exceeded"}), 429
        return (
            render_template(
                "auth/login.html",
                error="Demasiados intentos. Espera un minuto e intenta de nuevo.",
                next=request.form.get("next", request.args.get("next", "")),
                username=(request.form.get("username") or "").strip(),
            ),
            429,
        )

    @app.errorhandler(403)
    def _forbidden(error):
        if wants_json_response():
            return jsonify({"error": "forbidden"}), 403
        # Import diferido para evitar el ciclo app <-> app.routes.auth.
        template_kwargs = {}
        if current_user.is_authenticated:
            from app.routes.auth import _landing_url_for_role

            template_kwargs["home_url"] = _landing_url_for_role(current_user.role)
        return render_template("errors/403.html", **template_kwargs), 403

    return app
