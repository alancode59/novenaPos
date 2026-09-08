from flask import Flask
from app.config import Config
from app.extensions import init_db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    init_db(app)

    from app import models

    from app.routes.auth import auth_bp

    from app.routes.orders import orders_bp
    from app.routes.kitchen import kitchen_bp
    from app.routes.cashier import cashier_bp
    from app.routes.products import products_bp
    from app.routes.inventory import inventory_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(orders_bp, url_prefix="/orders")
    app.register_blueprint(kitchen_bp, url_prefix="/kitchen")
    app.register_blueprint(cashier_bp, url_prefix="/cashier")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")

    return app
