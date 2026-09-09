import sqlalchemy as sa

from app.extensions import db

# Lista cerrada de tamanos; CHECK (no ENUM) para poder ampliarla sin recrear el tipo.
PRODUCT_SIZE_VALUES = ("chica", "mediana", "grande", "unica")


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False, default="pizza", index=True)
    is_active = db.Column(db.Boolean, default=True)

    sizes = db.relationship(
        "ProductSize", backref="product", cascade="all, delete-orphan"
    )


class ProductSize(db.Model):
    # Unica fuente de verdad tamano->precio; reemplaza price_small/medium/large (bebida = fila 'unica').
    __tablename__ = "product_sizes"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, index=True
    )
    size = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("product_id", "size", name="uq_product_sizes_product_id_size"),
        sa.CheckConstraint(
            "size IN ('chica', 'mediana', 'grande', 'unica')",
            name="ck_product_sizes_size",
        ),
    )
