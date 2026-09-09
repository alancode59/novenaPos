from datetime import datetime

import sqlalchemy as sa

from app.extensions import db

# Lista cerrada de estados; CHECK y no ENUM (ver justificacion en el modelo User/migracion).
ORDER_STATUS_VALUES = ("taken", "kitchen", "ready", "delivered", "paid")


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey("tables.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="taken", index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Nullable: pedidos previos a esta columna no tienen dueno.
    created_by_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True, index=True
    )

    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")
    created_by = db.relationship("User")

    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('taken', 'kitchen', 'ready', 'delivered', 'paid')",
            name="ck_orders_status",
        ),
    )


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True
    )
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    # Reemplaza al texto libre: fija el tamano vendido y de ahi sale el precio.
    product_size_id = db.Column(
        db.Integer, db.ForeignKey("product_sizes.id"), nullable=False
    )
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    product_size = db.relationship("ProductSize")
    extras = db.relationship(
        "OrderItemExtra", backref="order_item", cascade="all, delete-orphan"
    )


class OrderItemExtra(db.Model):
    # Personalizacion de un item (agrega/quita ingrediente); unit_price congela el precio, igual que OrderItem.
    __tablename__ = "order_item_extras"

    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(
        db.Integer, db.ForeignKey("order_items.id"), nullable=False, index=True
    )
    inventory_item_id = db.Column(
        db.Integer, db.ForeignKey("inventory_items.id"), nullable=False, index=True
    )
    action = db.Column(db.String(10), nullable=False)
    quantity = db.Column(
        db.Numeric(10, 2), nullable=False, default=1, server_default=sa.text("1")
    )
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    inventory_item = db.relationship("InventoryItem")

    __table_args__ = (
        sa.CheckConstraint("action IN ('add', 'remove')", name="ck_order_item_extras_action"),
    )
