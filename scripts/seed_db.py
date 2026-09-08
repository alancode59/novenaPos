"""Script para poblar el catalogo inicial de productos en MySQL."""
from app import create_app
from app.extensions import db
from app.models import Product

app = create_app()

with app.app_context():
    db.session.add_all([
        Product(name="Margarita", category="pizza", price_small=89, price_medium=129, price_large=169),
        Product(name="Pepperoni", category="pizza", price_small=99, price_medium=139, price_large=179),
    ])
    db.session.commit()

print("Catalogo inicial insertado.")
