from datetime import datetime
from app.extensions import db

class FoodRecord(db.Model):
    __tablename__ = "food_records"

    id = db.Column(db.BigInteger, primary_key=True)

    daily_log_id = db.Column(
        db.BigInteger,
        db.ForeignKey("daily_energy_logs.id"),
        nullable=False
    )

    food_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Float, default=1)
    calorie = db.Column(db.Integer, nullable=False)

    # ai | manual
    input_method = db.Column(db.String(20), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

