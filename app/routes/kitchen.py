from flask import Blueprint, jsonify, render_template

from app.auth.decorators import roles_required

kitchen_bp = Blueprint("kitchen", __name__)


@kitchen_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "kitchen", "status": "ok"})


@kitchen_bp.route("/queue", methods=["GET"])
@roles_required("cocina", "admin")
def queue():
    """Landing de cocina: tablero de comandas. Vista minima, pendiente de contenido real."""
    return render_template("kitchen/queue.html")
