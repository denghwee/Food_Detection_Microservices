from datetime import datetime
from app.extensions import db

class Activity(db.Model):
    __tablename__ = "activities"

    id = db.Column(db.BigInteger, primary_key=True)

    daily_log_id = db.Column(
        db.BigInteger,
        db.ForeignKey("daily_energy_logs.id"),
        nullable=False
    )

    activity_type = db.Column(db.String(50), nullable=False)
    duration_minutes = db.Column(db.Integer)
    calorie_burned = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
