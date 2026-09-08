from flask import Blueprint, jsonify

kitchen_bp = Blueprint("kitchen", __name__)


@kitchen_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "kitchen", "status": "ok"})
