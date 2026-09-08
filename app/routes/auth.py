from flask import Blueprint, jsonify

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "auth", "status": "ok"})
