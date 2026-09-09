import sqlalchemy as sa

from app.extensions import db

TABLE_STATUS_VALUES = ("free", "occupied", "closing")


class RestaurantTable(db.Model):
    __tablename__ = "tables"

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default="free")

    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('free', 'occupied', 'closing')", name="ck_tables_status"
        ),
    )
