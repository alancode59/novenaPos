from flask import Blueprint, jsonify, render_template

from app.auth.decorators import roles_required

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "orders", "status": "ok"})


@orders_bp.route("/tables", methods=["GET"])
@roles_required("mesero", "admin")
def tables():
    """Landing de mesero: mapa de mesas. Vista minima, pendiente de contenido real."""
    return render_template("orders/tables.html")
