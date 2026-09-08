from flask import Blueprint, jsonify

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "inventory", "status": "ok"})
