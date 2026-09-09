"""Puebla el catalogo inicial de productos."""
from app import create_app
from app.extensions import db
from app.models import Product, ProductSize

# (nombre, categoria, [(tamano, precio), ...]) -- una bebida usa una sola fila 'unica'.
CATALOGO = [
    ("Margarita", "pizza", [("chica", 89), ("mediana", 129), ("grande", 169)]),
    ("Pepperoni", "pizza", [("chica", 99), ("mediana", 139), ("grande", 179)]),
]

app = create_app()

with app.app_context():
    for nombre, categoria, tamanos in CATALOGO:
        if db.session.scalar(db.select(Product).filter_by(name=nombre)):
            print(f"ya existia: {nombre}")
            continue
        producto = Product(name=nombre, category=categoria)
        producto.sizes = [ProductSize(size=t, price=p) for t, p in tamanos]
        db.session.add(producto)
    db.session.commit()

print("Catalogo inicial insertado.")
