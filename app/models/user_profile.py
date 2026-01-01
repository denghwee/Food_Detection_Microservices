from datetime import datetime
from app.extensions import db

from sqlalchemy import Enum as SAEnum

from app.enums.app_enum import ActivityLevelEnum, GoalTypeEnum


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False, unique=True, index=True)

    # relationship
    daily_energy_logs = db.relationship(
        "DailyEnergyLog",
        back_populates="user_profile",
        cascade="all, delete-orphan"
    )
    weight_histories = db.relationship(
        "UserProfileWeightHistory",
        back_populates="user_profile",
        cascade="all, delete-orphan"
    )
    gender = db.Column(db.String(10))
    date_of_birth = db.Column(db.Date)
    activity_level = db.Column(SAEnum(ActivityLevelEnum), nullable=False)
    aim_weight = db.Column(db.Double, nullable=False)
    aim_day = db.Column(db.DateTime)
    aim_day_end = db.Column(db.DateTime)
    day_of_activities = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
