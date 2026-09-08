from flask import Blueprint, jsonify, render_template

from app.auth.decorators import roles_required

cashier_bp = Blueprint("cashier", __name__)


@cashier_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "cashier", "status": "ok"})


@cashier_bp.route("/pending", methods=["GET"])
@roles_required("caja", "admin")
def pending():
    """Landing de caja: cuentas por cobrar. Vista minima, pendiente de contenido real."""
    return render_template("cashier/pending.html")
