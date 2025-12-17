from datetime import datetime
from app.extensions import db

from sqlalchemy import Enum as SAEnum

from app.enums.app_enum import ActivityLevelEnum, GoalTypeEnum


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.BigInteger, primary_key=True)
    user_email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    gender = db.Column(db.String(10))
    date_of_birth = db.Column(db.Date)

    activity_level = db.Column(SAEnum(ActivityLevelEnum), nullable=False, default=ActivityLevelEnum.sedentary)
    goal_type = db.Column(SAEnum(GoalTypeEnum), nullable=False, default=GoalTypeEnum.maintain)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
