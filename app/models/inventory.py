from app.extensions import db


class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    stock = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    unit = db.Column(db.String(20), nullable=False, default="kg")
    min_threshold = db.Column(db.Numeric(10, 2), nullable=False, default=0)
