from app.extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False, default="pizza")
    price_small = db.Column(db.Numeric(10, 2), nullable=True)
    price_medium = db.Column(db.Numeric(10, 2), nullable=True)
    price_large = db.Column(db.Numeric(10, 2), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
