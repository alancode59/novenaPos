import sqlalchemy as sa

from app.extensions import db


class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    stock = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    unit = db.Column(db.String(20), nullable=False, default="kg")
    min_threshold = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    # Vendible como extra (ej. queso); la harina se queda en False y no aparece en el menu de extras.
    is_offerable_extra = db.Column(
        db.Boolean, nullable=False, default=False, server_default=sa.text("false")
    )
    # Precio del extra; solo tiene sentido si is_offerable_extra es True.
    extra_price = db.Column(db.Numeric(10, 2), nullable=True)


class ProductIngredient(db.Model):
    # La receta: cuelga de product_size (no de product) porque una grande lleva mas queso que una chica.
    __tablename__ = "product_ingredients"

    id = db.Column(db.Integer, primary_key=True)
    product_size_id = db.Column(
        db.Integer, db.ForeignKey("product_sizes.id"), nullable=False, index=True
    )
    inventory_item_id = db.Column(
        db.Integer, db.ForeignKey("inventory_items.id"), nullable=False, index=True
    )
    # Cantidad en la unidad de inventory_items.unit para esa combinacion producto+tamano.
    quantity = db.Column(db.Numeric(10, 2), nullable=False)

    product_size = db.relationship("ProductSize", backref="ingredients")
    inventory_item = db.relationship("InventoryItem")

    __table_args__ = (
        db.UniqueConstraint(
            "product_size_id", "inventory_item_id", name="uq_product_ingredients_size_item"
        ),
    )
