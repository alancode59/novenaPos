from datetime import datetime
from app.extensions import db


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    method = db.Column(db.String(20), nullable=False)  # efectivo, tarjeta, transferencia
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    tip = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
