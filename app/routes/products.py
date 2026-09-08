from flask import Blueprint, jsonify, render_template

from app.auth.decorators import roles_required

products_bp = Blueprint("products", __name__)


@products_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "products", "status": "ok"})


@products_bp.route("/dashboard", methods=["GET"])
@roles_required("admin")
def dashboard():
    """Landing de admin: resumen de catalogo. Vista minima, pendiente de contenido real."""
    return render_template("products/dashboard.html")
