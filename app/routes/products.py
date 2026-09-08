from flask import Blueprint, jsonify

products_bp = Blueprint("products", __name__)


@products_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "products", "status": "ok"})
