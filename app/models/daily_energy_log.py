from datetime import datetime, date
from app.extensions import db

class DailyEnergyLog(db.Model):
    __tablename__ = "daily_energy_logs"

    id = db.Column(db.BigInteger, primary_key=True)
    user_email = db.Column(db.String(255), nullable=False, index=True)
    log_date = db.Column(db.Date, nullable=False)
    total_steps = db.Column(db.Integer, default=0)
    total_calorie_in = db.Column(db.Integer, default=0)
    base_calorie_out = db.Column(db.Integer, default=0)
    tdee = db.Column(db.Integer, default=0)
    target_calorie = db.Column(db.Integer, default=0)
    activity_calorie_out = db.Column(db.Integer, default=0)
    net_calorie = db.Column(db.Integer, default=0)
    steps_calorie_out = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_email", "log_date", name="uk_user_date"),
    )

