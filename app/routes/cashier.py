from flask import Blueprint, jsonify

cashier_bp = Blueprint("cashier", __name__)


@cashier_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "cashier", "status": "ok"})
