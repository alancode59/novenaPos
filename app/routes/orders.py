from flask import Blueprint, jsonify

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "orders", "status": "ok"})
