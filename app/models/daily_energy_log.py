from datetime import datetime, date
from app.extensions import db

class DailyEnergyLog(db.Model):
    __tablename__ = "daily_energy_logs"

    id = db.Column(db.BigInteger, primary_key=True)

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("user_profiles.user_id"),
        nullable=False,
        index=True
    )

    # relationship
    user_profile = db.relationship(
        "UserProfile",
        back_populates="daily_energy_logs"
    )
    food_records = db.relationship(
        "FoodRecord",
        back_populates="daily_log",
        cascade="all, delete-orphan"
    )
    log_date = db.Column(db.Date, nullable=False)
    total_steps = db.Column(db.Integer, default=0)
    total_calorie_in = db.Column(db.Integer, default=0)
    tdee = db.Column(db.Integer, default=0)
    target_calorie = db.Column(db.Integer, default=0)
    steps_calorie_out = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "log_date", name="uk_user_date"),
    )



