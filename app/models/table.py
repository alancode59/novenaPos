from app.extensions import db


class RestaurantTable(db.Model):
    __tablename__ = "tables"

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default="free")  # free, occupied, closing
